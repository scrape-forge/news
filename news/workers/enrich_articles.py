"""Enrich news articles with structured Papagon Insight intelligence."""

import json
import os

from dotenv import load_dotenv
from psycopg2.extras import Json

from news.workers.common.database import get_db_connection
from news.workers.common.groq import request_json_completion


DEFAULT_BATCH_SIZE = 5
MAX_ALLOWED_BATCH_SIZE = 5
DEFAULT_MAX_REQUESTS = 12
MAX_ALLOWED_REQUESTS = 15
MIN_REMAINING_TOKENS = 3000
MIN_REMAINING_REQUESTS = 2
ENTITY_GROUPS = ("companies", "people", "locations")


def _bounded_setting(
    value: int | None,
    *,
    env_name: str,
    default: int,
    maximum: int,
) -> int:
    raw_value = value if value is not None else os.getenv(env_name, str(default))
    try:
        parsed_value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{env_name} must be an integer") from exc
    if parsed_value < 1:
        raise ValueError(f"{env_name} must be at least 1")
    return min(parsed_value, maximum)


def fetch_unenriched_articles(cursor, limit: int, attempted_ids: set[int] | None = None):
    """Claim an enrichment batch until the transaction ends."""
    cursor.execute(
        """
        SELECT id, title, COALESCE(summary, ''), COALESCE(tags, '{}')
        FROM news_articles
        WHERE ai_enriched_at IS NULL
          AND NOT (id = ANY(%s))
        ORDER BY date_post DESC
        LIMIT %s
        FOR UPDATE SKIP LOCKED;
        """,
        (list(attempted_ids or set()), limit),
    )
    return cursor.fetchall()


def _enrichment_messages(articles) -> list[dict[str, str]]:
    system_prompt = (
        "You are Papagon Insight, an Indonesian news intelligence system. "
        "For EACH supplied article return structured, factual intelligence in "
        "Indonesian. Return ONLY one JSON object keyed by the article id. Each "
        "value must contain: tags (2-4 short standardized topic strings), "
        "sentiment (number from -1.0 to 1.0 measuring economic/market impact), "
        "sentiment_label (Positive, Neutral, or Negative), bullets (exactly 2 "
        "concise executive-summary strings), entities (an object containing "
        "companies, people, and locations arrays), and sector (one concise "
        "industry or policy sector). Do not invent facts not present in the "
        "headline or summary. Example value: {\"tags\":[\"Suku Bunga BI\"],"
        "\"sentiment\":0.4,\"sentiment_label\":\"Positive\","
        "\"bullets\":[\"Fakta utama.\",\"Dampak utama.\"],"
        "\"entities\":{\"companies\":[],\"people\":[],"
        "\"locations\":[\"Jakarta\"]},\"sector\":\"Banking & Finance\"}."
    )
    items = [
        {
            "id": str(article[0]),
            "title": article[1],
            "summary": article[2],
            "existing_tags": article[3],
        }
        for article in articles
    ]
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(items, ensure_ascii=False)},
    ]


def call_groq_batch(articles, api_key: str):
    result = request_json_completion(
        api_key=api_key,
        messages=_enrichment_messages(articles),
        response_format={"type": "json_object"},
    )

    if result.usage:
        print(
            "📊 [Groq Tokens] "
            f"Prompt: {result.usage.get('prompt_tokens', 0)} | "
            f"Output: {result.usage.get('completion_tokens', 0)} | "
            f"Total: {result.usage.get('total_tokens', 0)} "
            f"(Remaining TPM: {result.remaining_tokens}, "
            f"RPM: {result.remaining_requests})",
            flush=True,
        )

    quota_exhausted = result.status_code == 429 or (
        result.remaining_tokens is not None
        and result.remaining_tokens < MIN_REMAINING_TOKENS
    ) or (
        result.remaining_requests is not None
        and result.remaining_requests < MIN_REMAINING_REQUESTS
    )
    if result.error:
        retry = f" Retry after {result.retry_after}s." if result.retry_after else ""
        print(
            f"⚠️ [Enrichment Worker] Request failed "
            f"(HTTP {result.status_code or 'unknown'}): {result.error}.{retry}",
            flush=True,
        )

    enrichment_map = result.content if isinstance(result.content, dict) else {}
    return enrichment_map, quota_exhausted


def _clean_strings(value, *, maximum: int | None = None) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned = []
    for item in value:
        if isinstance(item, str) and item.strip():
            normalized = item.strip()
            if normalized not in cleaned:
                cleaned.append(normalized)
    return cleaned[:maximum] if maximum is not None else cleaned


def normalize_enrichment(value, existing_tags: list[str] | None = None):
    if not isinstance(value, dict):
        return None

    new_tags = [tag.title() for tag in _clean_strings(value.get("tags"), maximum=4)]
    tags = _clean_strings([*(existing_tags or []), *new_tags])
    bullets = _clean_strings(value.get("bullets"), maximum=2)
    sector = value.get("sector")
    entities = value.get("entities")
    try:
        sentiment = float(value.get("sentiment"))
    except (TypeError, ValueError):
        return None

    if not -1.0 <= sentiment <= 1.0 or len(bullets) != 2:
        return None
    if not isinstance(sector, str) or not sector.strip() or not isinstance(entities, dict):
        return None

    clean_entities = {
        group: _clean_strings(entities.get(group))
        for group in ENTITY_GROUPS
    }
    label = "Positive" if sentiment > 0.1 else "Negative" if sentiment < -0.1 else "Neutral"
    return {
        "tags": tags,
        "sentiment_score": sentiment,
        "sentiment_label": label,
        "ai_bullets": bullets,
        "entities": clean_entities,
        "sector": sector.strip()[:100],
    }


def update_article_enrichments(
    cursor,
    conn,
    enrichment_map: dict,
    claimed_articles: dict[int, list[str]],
) -> int:
    query = """
        UPDATE news_articles
        SET tags = %s,
            sentiment_score = %s,
            sentiment_label = %s,
            ai_bullets = %s,
            entities = %s,
            sector = %s,
            ai_enriched_at = NOW()
        WHERE id = %s AND ai_enriched_at IS NULL;
    """
    updated_count = 0
    for article_id, value in enrichment_map.items():
        try:
            parsed_id = int(article_id)
        except (TypeError, ValueError):
            continue
        if parsed_id not in claimed_articles:
            continue
        enrichment = normalize_enrichment(value, claimed_articles[parsed_id])
        if enrichment is None:
            continue
        cursor.execute(
            query,
            (
                enrichment["tags"],
                enrichment["sentiment_score"],
                enrichment["sentiment_label"],
                enrichment["ai_bullets"],
                Json(enrichment["entities"]),
                enrichment["sector"],
                parsed_id,
            ),
        )
        updated_count += cursor.rowcount
    conn.commit()
    return updated_count


def run(batch_size: int | None = None, max_requests: int | None = None) -> int:
    load_dotenv()
    try:
        batch_size = _bounded_setting(
            batch_size,
            env_name="BATCH_SIZE",
            default=DEFAULT_BATCH_SIZE,
            maximum=MAX_ALLOWED_BATCH_SIZE,
        )
        max_requests = _bounded_setting(
            max_requests,
            env_name="MAX_RPM",
            default=DEFAULT_MAX_REQUESTS,
            maximum=MAX_ALLOWED_REQUESTS,
        )
    except ValueError as exc:
        print(f"❌ [Enrichment Worker] Invalid configuration: {exc}", flush=True)
        return 2

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ℹ️ [Enrichment Worker] GROQ_API_KEY not configured. Exiting.", flush=True)
        return 0

    print(
        f"🚀 [Enrichment Worker] Run started (Max Requests: {max_requests}, "
        f"Batch Size: {batch_size})...",
        flush=True,
    )
    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"❌ [Enrichment Worker] DB connection failed: {exc}", flush=True)
        return 1

    total_enriched = 0
    request_count = 0
    attempted_ids: set[int] = set()
    try:
        with conn.cursor() as cursor:
            for _ in range(max_requests):
                articles = fetch_unenriched_articles(
                    cursor,
                    limit=batch_size,
                    attempted_ids=attempted_ids,
                )
                if not articles:
                    conn.rollback()
                    print("✅ [Enrichment Worker] All articles enriched.", flush=True)
                    break

                request_count += 1
                attempted_ids.update(article[0] for article in articles)
                enrichment_map, quota_exhausted = call_groq_batch(articles, api_key)
                if enrichment_map:
                    updated = update_article_enrichments(
                        cursor,
                        conn,
                        enrichment_map,
                        claimed_articles={article[0]: article[3] for article in articles},
                    )
                    total_enriched += updated
                    print(
                        f"✅ [Enrichment Worker] Req #{request_count}/{max_requests}: "
                        f"Enriched {updated}/{len(articles)} articles.",
                        flush=True,
                    )
                else:
                    conn.rollback()
                    print(
                        f"⚠️ [Enrichment Worker] Req #{request_count}/{max_requests}: "
                        "Empty or failed response.",
                        flush=True,
                    )

                if quota_exhausted:
                    print("🛑 [Enrichment Worker] API quota safeguard reached.", flush=True)
                    break
    except Exception as exc:
        conn.rollback()
        print(f"❌ [Enrichment Worker] Unexpected failure: {exc}", flush=True)
        return 1
    finally:
        conn.close()

    print(
        f"🎉 [Enrichment Worker] Run finished: {total_enriched} articles "
        f"enriched across {request_count} API requests.",
        flush=True,
    )
    return 0
