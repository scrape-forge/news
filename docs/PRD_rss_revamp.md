# PRD — News Scraper RSS Revamp
**Project:** `scrape-forge/news`
**Version:** 2.1
**Date:** 2026-08-12
**Status:** 🟡 In progress

---

## 1. Background & Problem Statement

The original news scraper relied entirely on **HTML web scraping** for all 12 Indonesian news sources. This approach had several problems:

| Problem | Impact |
|---|---|
| Legally grey — violates ToS of most sites | Risk of cease & desist or legal liability |
| `ROBOTSTXT_OBEY = False` — ignores robots.txt | Potential UU ITE violation |
| No rate limiting — hammers servers | Risk of IP ban, potential UU ITE Pasal 30/33 |
| CSS selectors break when sites redesign | Maintenance burden, data gaps |
| 4 of 12 sources have no usable public RSS | Must keep scraping those selectively |
| Pipelines disabled by default | No data actually stored in current state |

**8 out of 12 sources have working publisher RSS feeds** that provide richer data (images, excerpts) than the HTML scrapers. Detik, Liputan6, and Tempo were added after their current feed URLs were validated with live items. The remaining sources use public news sitemaps for all-category discovery and rate-limited article pages for metadata; Jawapos's API is not used because it disallows crawlers.

---

## 2. Goals

### Primary Goals
- ✅ Replace HTML scrapers with RSS readers for all sources that have official RSS feeds
- ✅ Make the project legally compliant for educational & research use
- ✅ Enrich the data model with new fields available from RSS (`image`, `summary`)
- ✅ Fix all broken pipelines so data is actually stored correctly for all 12 sources
- ✅ Add rate limiting and robots.txt compliance for remaining scrapers

### Secondary Goals
- ✅ Unify data normalization logic across all sources
- ✅ Add configurable scheduling (run on interval, not just once)
- ✅ Improve error handling and logging
- ✅ Separate dev dependencies from production requirements

### Non-Goals (Out of Scope for v2.0)
- ❌ Full article body extraction
- ❌ NLP / sentiment analysis
- ❌ Frontend / website UI (separate project)
- ❌ Paid API integration (Antara official API)

---

## 3. Source Strategy

### Group A — Replace with RSS (8 sources)

> Full spider replacement. No HTML scraping needed.

| Source | Spider File | RSS URL | RSS Quality |
|---|---|---|---|
| Antara | `antara.py` | `https://www.antaranews.com/rss/terkini.xml` | ✅ Rich (image, excerpt, content) |
| Detik | `detik.py` | `https://news.detik.com/rss` | ✅ Rich (image, excerpt) |
| Tribunnews | `tribun.py` | `https://www.tribunnews.com/rss` | ✅ Good (image, excerpt) |
| Sindonews | `sindo.py` | `https://sindikasi.sindonews.com/` | ✅ Rich (image, excerpt, category) |
| Republika | `republika.py` | `https://www.republika.co.id/rss/nasional/` | ✅ Rich (author, image, content) |
| Okezone | `okezone.py` | `https://sindikasi.okezone.com/index.php/rss/0/RSS2.0` | ✅ Good |
| Liputan6 | `liputan6.py` | `https://feed.liputan6.com/rss/news` | ✅ Rich (image, excerpt, category) |
| Tempo | `tempo.py` | `https://rss.tempo.co/nasional` | ✅ Good (image, excerpt) |

### Group B — Public Sitemap + Rate-Limited Article Pages (4 sources)

> No official RSS. Keep existing spider but fix settings and add rate limiting.

| Source | Spider File | Why No RSS | Fix Required |
|---|---|---|---|
| Jawapos | `jawapos.py` | Former RSS URLs redirect to HTML with zero items | Use public recent-post sitemap |
| Kompas | `kompas.py` | Feed API requires a currently invalid API key | Use all public news sitemaps |
| Merdeka | `merdeka.py` | `/feed` and `/rss` return 404 | Use all category news sitemaps |
| Suara | `suara.py` | RSS paths redirect to non-feed pages | Use every category news sitemap |

---

## 4. Data Model Changes

### Current `NewsItem` (v1)
```python
class NewsItem(scrapy.Item):
    title                = scrapy.Field()
    author               = scrapy.Field()
    date_post            = scrapy.Field()   # UTC datetime
    date_post_local_time = scrapy.Field()   # string
    link                 = scrapy.Field()
    content              = scrapy.Field()   # defined but never populated
    tags                 = scrapy.Field()
    source               = scrapy.Field()
```

### Proposed `NewsItem` (v2)
```python
class NewsItem(scrapy.Item):
    # --- Existing fields (kept) ---
    title                = scrapy.Field()   # Article headline
    author               = scrapy.Field()   # Author name (optional)
    date_post            = scrapy.Field()   # Publication datetime (UTC)
    date_post_local_time = scrapy.Field()   # Raw local datetime string
    link                 = scrapy.Field()   # Canonical article URL
    tags                 = scrapy.Field()   # Publisher topics; may be empty
    source               = scrapy.Field()   # Spider name

    # --- New fields from RSS ---
    summary              = scrapy.Field()   # Short excerpt/description (NEW)
    image_url            = scrapy.Field()   # Thumbnail image URL (NEW)

    # --- Removed ---
    # content → removed (was never populated, misleading)
```

### Field Availability by Source

| Field | Group A (RSS) | Group B (Scraper) |
|---|---|---|
| `title` | ✅ | ✅ |
| `link` | ✅ | ✅ |
| `date_post` | ✅ | ✅ |
| `date_post_local_time` | ✅ | ✅ |
| `source` | ✅ | ✅ |
| `author` | ⚠️ Partial | ✅ Full |
| `tags` | ⚠️ Partial | ✅ Full |
| `summary` | ✅ **NEW** | ❌ Not available |
| `image_url` | ✅ **NEW** | ❌ Not available |

---

## 5. Technical Requirements

### 5.1 New: RSS Spider Base Class

Create a reusable base class `news/spiders/base_rss.py`:

```python
class RSSBaseSpider(scrapy.Spider):
    """
    Base class for RSS-based spiders.
    Subclasses only need to define:
      - name
      - rss_url (str or list of str)
      - source (str)
    """
    rss_url: str | list[str]

    def start_requests(self): ...
    def parse(self, response): ...         # parse RSS XML
    def parse_item(self, entry) -> NewsItem: ...  # normalize fields
    def get_title(self, entry): ...
    def get_link(self, entry): ...
    def get_date(self, entry): ...
    def get_author(self, entry): ...
    def get_tags(self, entry): ...
    def get_summary(self, entry): ...
    def get_image(self, entry): ...
```

### 5.2 New: Group A Spider Structure

Each Group A spider becomes minimal:

```python
# news/spiders/antara.py (v2)
from news.spiders.base_rss import RSSBaseSpider

class AntaraSpider(RSSBaseSpider):
    name = 'antara'
    rss_url = 'https://www.antaranews.com/rss/terkini.xml'
    source = 'antara'
```

### 5.3 Fix: Group B Spider Issues

| Spider | Bug to Fix |
|---|---|
| `detik.py` | Line 40: broken pagination URL (`?date=...?page=N`) → use `urlencode` properly |
| `kompas.py` | Line 22: infinite pagination → add stop condition when page has no articles |
| `antara.py` | Lines 33–37: over-fetches all pages at once → use incremental `next_page` |
| All Group B | Add `DOWNLOAD_DELAY` per-spider via `custom_settings` |

### 5.4 Fix: Settings (`settings.py`)

```python
# REQUIRED CHANGES

# Compliance
ROBOTSTXT_OBEY = True             # was: False

# Rate limiting  
DOWNLOAD_DELAY = 2                 # was: not set
AUTOTHROTTLE_ENABLED = True        # was: False
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
CONCURRENT_REQUESTS_PER_DOMAIN = 1 # was: not set

# User-Agent rotation (UNCOMMENT)
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
    'scrapy_fake_useragent.middleware.RetryUserAgentMiddleware': 401,
}

# Enable pipelines (UNCOMMENT and fix)
ITEM_PIPELINES = {
    'news.pipelines.NewsPipeline': 300,         # MongoDB
    # 'news.pipelines.ElasticSearchPipeline': 500  # Elasticsearch (optional)
}
```

### 5.5 Fix: `NewsPipeline` (MongoDB)

Current pipeline only handles `detik` and `kompas`. Must be generalized:

```python
# pipelines.py (v2)
def process_item(self, item, spider):
    # Use source name as collection (works for ALL spiders)
    collection_name = f"{item['source']}-news"
    self.db[collection_name].update_one(
        {'link': item['link']},        # deduplicate by URL
        {'$set': dict(item)},
        upsert=True
    )
    return item
```

### 5.6 Fix: `ElasticSearchPipeline`

```python
# Use ELASTICSEARCH_UNIQ_KEY consistently
# Remove unused es_type parameter
# Add open_spider / close_spider for proper lifecycle
# Fix: settings has ELASTICSEARCH_UNIQ_KEY = 'url' but pipeline uses item['link']
#      → standardize to 'link'
```

### 5.7 Fix: `requirements.txt`

```
# Remove unused packages:
- pyes==0.99.6           (unmaintained, not used)
- ScrapyElasticSearch==0.9.2  (not used, custom pipeline instead)

# Move to dev-requirements.txt:
- autopep8==1.6.0
- pycodestyle==2.8.0

# Upgrade:
- elasticsearch==7.0.0  →  elasticsearch==8.x or pin to match actual ES version
```

---

## 6. New File Structure (v2)

```
news/
├── items.py                  # Updated NewsItem with summary, image_url
├── lib.py                    # Shared utilities (minimal changes)
├── middlewares.py            # No changes
├── pipelines.py              # Fixed: generic collection + upsert
├── settings.py               # Fixed: rate limiting, pipelines enabled
└── spiders/
    ├── __init__.py
    ├── base_rss.py           # NEW: reusable RSS base spider
    │
    ├── # Group A — 8 RSS spiders (minimal, extends base_rss)
    ├── antara.py             # REFACTORED
    ├── tribun.py             # REFACTORED
    ├── sindo.py              # REFACTORED
    ├── republika.py          # REFACTORED
    ├── okezone.py            # REFACTORED
    ├── detik.py              # REFACTORED
    ├── liputan6.py           # REFACTORED
    ├── tempo.py              # REFACTORED
    │
    └── # Group B — public sitemap + rate-limited article spiders
    ├── jawapos.py            # Recent-post sitemap
    ├── kompas.py             # All news sitemaps
    ├── merdeka.py            # All category news sitemaps
    └── suara.py              # All category news sitemaps

requirements.txt              # CLEANED
dev-requirements.txt          # NEW
```

---

## 7. Migration Plan

### Phase 1 — Foundation (Day 1)
- [ ] Update `NewsItem` — add `summary`, `image_url`, remove `content`
- [ ] Fix `settings.py` — enable rate limiting, user-agent, robots.txt
- [ ] Fix `NewsPipeline` — generic collection name + upsert dedup
- [ ] Fix `ElasticSearchPipeline` — lifecycle hooks, key consistency
- [ ] Clean `requirements.txt` — remove unused, split dev deps

### Phase 2 — RSS Base Class (Day 2)
- [ ] Create `news/spiders/base_rss.py`
- [ ] Write unit tests for RSS parsing helpers
- [ ] Validate with Antara feed (richest RSS, best for testing)

### Phase 3 — Group A Spider Refactor (Day 3)
- [ ] Refactor `antara.py` → RSS
- [ ] Refactor `tribun.py` → RSS
- [ ] Refactor `sindo.py` → RSS
- [ ] Refactor `republika.py` → RSS
- [ ] Refactor `okezone.py` → RSS
- [x] Refactor `detik.py` → RSS
- [x] Refactor `liputan6.py` → RSS
- [x] Refactor `tempo.py` → RSS

### Phase 4 — Group B Spider Fixes (Day 4)
- [ ] Fix `kompas.py` infinite pagination
- [ ] Fix `antara.py` over-fetching (now Group A, but fix pattern in others)
- [ ] Add `custom_settings` rate limiting to all Group B spiders

### Phase 5 — Validation & Cleanup (Day 5)
- [ ] Run all 12 spiders, verify output to MongoDB
- [ ] Verify deduplication works (run same spider twice)
- [ ] Verify Elasticsearch pipeline
- [ ] Update README.md with v2 architecture
- [ ] Tag release as `v2.0.0`

---

## 8. Acceptance Criteria

| # | Criteria | How to Verify |
|---|---|---|
| AC-1 | All 8 Group A spiders read from RSS, not HTML | Code review — no CSS selectors |
| AC-2 | `image_url` and `summary` populated for Group A | `scrapy crawl antara -o out.json` → check fields |
| AC-3 | All 12 spiders store to correct MongoDB collection | Check DB: `{source}-news` collections exist |
| AC-4 | Running same spider twice → no duplicate documents | `upsert=True` on `link` field |
| AC-5 | `ROBOTSTXT_OBEY = True` in settings | Code review |
| AC-6 | `DOWNLOAD_DELAY = 2` minimum in settings | Code review |
| AC-7 | `RandomUserAgentMiddleware` enabled for HTML spiders | Code review |
| AC-8 | `detik` RSS produces current, normalized items | Live crawl + field check |
| AC-9 | `kompas` spider stops crawling when no more articles | Manual test — no infinite loop |
| AC-10 | `pyes` and `ScrapyElasticSearch` removed from requirements | `pip check` passes |
| AC-11 | Every spider emits only the rolling last 24 hours | Check oldest/newest exported `date_post` |
| AC-12 | Group B discovers every publisher sitemap category | Inspect category coverage in crawl output |

---

## 9. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| RSS feed goes down | Medium | Medium | Add retry + fallback to scraper |
| RSS feed URL changes | Low | High | Monitor feed health, add alert |
| Group B sites block IP | Medium | Medium | Rate limiting + user-agent rotation |
| Republika feed is stale (last seen: 5 Jul 2026) | High | Medium | Monitor `lastBuildDate`, alert if >24h old |
| A publisher sitemap omits recent items | Low | Medium | Enforce detail-date checks and monitor daily item counts |

---

## 10. Out of Scope / Future Considerations (v3+)

- 🔜 Web UI / dashboard for the scraped data
- 🔜 Scheduling system (cron / Celery) for continuous crawling
- 🔜 NLP pipeline — topic clustering, sentiment analysis
- 🔜 Deduplication across sources (same story, different outlets)
- 🔜 Official Antara API integration (paid)
- 🔜 Content partnership outreach to Detik, Kompas
- 🔜 Docker / containerization
- 🔜 Export formats: CSV, Parquet for research datasets
