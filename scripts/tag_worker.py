# -*- coding: utf-8 -*-
"""
RPM-Aware AI Tag Worker Script.
Batch-processes untagged articles in PostgreSQL using Groq's Free Llama-3.1 API.
Controls requests per minute (MAX_RPM) with dynamic sleep spacing.
Designed to be triggered by Crontab every 1 minute.
"""

import json
import os
import sys
import time
import psycopg2
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Force unbuffered real-time log flushing for crontab & tail -f
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(line_buffering=True)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.1-8b-instant"

# Rate & Batch Configuration from Environment
# TPM Safety: 10 items ~ 1,000 tokens. 5 calls = 5,000 tokens (Safely under 6,000 TPM limit)
DEFAULT_BATCH_SIZE = 10
MAX_ALLOWED_BATCH_SIZE = 15
BATCH_SIZE = min(int(os.getenv('BATCH_SIZE', DEFAULT_BATCH_SIZE)), MAX_ALLOWED_BATCH_SIZE)

# Max RPM allowed per minute run
MAX_RPM = min(int(os.getenv('MAX_RPM', '12')), 15)




def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        dbname=os.getenv('POSTGRES_DB', 'news_db'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', '')
    )


def fetch_untagged_articles(cursor, limit=BATCH_SIZE):
    query = """
        SELECT id, title, COALESCE(summary, '') 
        FROM news_articles 
        WHERE tags IS NULL OR array_length(tags, 1) IS NULL OR array_length(tags, 1) = 0
        ORDER BY date_post DESC 
        LIMIT %s;
    """
    cursor.execute(query, (limit,))
    return cursor.fetchall()


def call_groq_batch(articles, api_key):
    system_prompt = (
        "You are an Indonesian news categorization system. "
        "You will receive a JSON list of news articles with 'id', 'title', and 'summary'. "
        "For EACH article, extract 2 to 4 standardized Indonesian topic tags (e.g. 'IKN', 'Pilkada', 'Suku Bunga BI', 'Inflasi', 'Ekonomi', 'Teknologi', 'Politik', 'Otomotif', 'Sepakbola'). "
        "Return ONLY a JSON object mapping article 'id' string to array of string tags. "
        "Example output: {\"12\": [\"IKN\", \"Politik\"], \"13\": [\"Ekonomi\", \"Inflasi\"]}"
    )

    items_payload = [
        {"id": str(art[0]), "title": art[1], "summary": art[2]}
        for art in articles
    ]

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(items_payload, ensure_ascii=False)}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=8)
        if response.status_code == 200:
            res_data = response.json()
            content = res_data['choices'][0]['message']['content'].strip()
            
            # Extract token usage details
            usage = res_data.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            comp_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)
            
            # Extract rate limit headers from Groq
            rem_tpm_raw = response.headers.get('x-ratelimit-remaining-tokens')
            rem_rpm_raw = response.headers.get('x-ratelimit-remaining-requests')

            rem_tpm = int(rem_tpm_raw) if rem_tpm_raw and rem_tpm_raw.isdigit() else 9999
            rem_rpm = int(rem_rpm_raw) if rem_rpm_raw and rem_rpm_raw.isdigit() else 99

            print(f"📊 [Groq Tokens] Prompt: {prompt_tokens} | Output: {comp_tokens} | Total: {total_tokens} (Remaining TPM: {rem_tpm}, RPM: {rem_rpm})", flush=True)

            # Safeguard: If remaining TPM is under 1,500 (25% of 6,000 TPM limit) or RPM under 2, stop immediately
            quota_exhausted = (rem_tpm < 1500) or (rem_rpm < 2)
            if quota_exhausted:
                print(f"⚠️ [Groq Safeguard] Almost reached 6,000 TPM limit! (Remaining TPM: {rem_tpm}/6000, RPM: {rem_rpm}/30). Halting requests for this run.", flush=True)

            return json.loads(content), quota_exhausted

        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 6))
            print(f"⚠️ [Groq Worker] Rate limited (HTTP 429). Retry after {retry_after}s.", flush=True)
            return {}, True
        else:
            print(f"⚠️ [Groq Worker] API HTTP {response.status_code}: {response.text[:100]}", flush=True)
    except Exception as exc:
        print(f"⚠️ [Groq Worker] Request failed: {exc}", flush=True)

    return {}, False




def update_article_tags(cursor, conn, tag_map):
    updated_count = 0
    query = "UPDATE news_articles SET tags = %s WHERE id = %s;"
    for art_id_str, tags in tag_map.items():
        try:
            art_id = int(art_id_str)
            if isinstance(tags, list) and tags:
                clean_tags = [str(t).strip().title() for t in tags if isinstance(t, str)]
                cursor.execute(query, (clean_tags, art_id))
                updated_count += 1
        except (ValueError, TypeError):
            continue
    conn.commit()
    return updated_count


def main():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ℹ️ [Groq Worker] GROQ_API_KEY not configured. Exiting.", flush=True)
        return

    print(f"🚀 [Groq Worker] Run started (MAX_RPM: {MAX_RPM}, Batch Size: {BATCH_SIZE}, Zero Delay)...", flush=True)


    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"❌ [Groq Worker] DB connection failed: {exc}", flush=True)
        return

    total_tagged = 0
    request_count = 0

    with conn.cursor() as cursor:
        for request_num in range(1, MAX_RPM + 1):
            articles = fetch_untagged_articles(cursor, limit=BATCH_SIZE)
            if not articles:
                print("✅ [Groq Worker] All untagged articles processed. Exiting early.", flush=True)
                break

            request_count += 1
            start_time = time.time()
            tag_map, quota_exhausted = call_groq_batch(articles, api_key)
            
            if tag_map:
                updated = update_article_tags(cursor, conn, tag_map)
                total_tagged += updated
                print(f"✅ [Groq Worker] Req #{request_count}/{MAX_RPM}: Tagged {updated}/{len(articles)} articles.", flush=True)
            else:
                print(f"⚠️ [Groq Worker] Req #{request_count}/{MAX_RPM}: Empty or failed response.", flush=True)

            if quota_exhausted:
                print("🛑 [Groq Safeguard] Stopping further requests in this run to prevent HTTP 429.", flush=True)
                break



    conn.close()
    print(f"🎉 [Groq Worker] Run finished: {total_tagged} articles tagged across {request_count} API requests.", flush=True)


if __name__ == '__main__':
    main()
