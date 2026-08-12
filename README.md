# 📰 News Scraper v2.0

A hybrid RSS and web scraping framework built with [Scrapy](https://scrapy.org/) for collecting news articles from Indonesian news portals. Built for **educational and research purposes only**.

> ⚠️ **Disclaimer**: This project is intended for educational purposes only. Always respect the Terms of Service of any website you interact with. The author is not responsible for any misuse of this tool.

---

## 🚀 Features (v2.0)

- **Hybrid Architecture (Legal & Stable)**: Uses publisher RSS feeds for 8 sources, falling back to public news sitemaps and rate-limited article pages for the remaining 4.
- **Compliance First**: `ROBOTSTXT_OBEY` enabled, dynamic download delays (`AUTOTHROTTLE`), and domain concurrency limits.
- **Enriched Data**: Extracts `image_url` and `summary` (excerpts) natively from RSS feeds.
- **Consistent Time Window**: Every spider emits articles from the most recent 24 hours across all configured categories.
- **Unified Pipelines**: MongoDB and Elasticsearch pipelines that handle all 12 spiders with built-in deduplication.
- **Rotating User-Agent**: Built-in via `scrapy-fake-useragent`.

---

## 🕷️ Supported Sources

**Group A: RSS-based (richer data)**
- `antara`, `detik`, `liputan6`, `okezone`, `republika`, `sindo`, `tempo`, `tribun`

**Group B: Sitemap + HTML Spiders (Rate-limited)**
- `jawapos`, `kompas`, `merdeka`, `suara`

---

## 🗂️ Project Structure

```
.
├── requirements.txt      # Production dependencies
├── dev-requirements.txt  # Linter/formatting tools
├── PRD_rss_revamp.md     # v2.0 architecture details
├── scrapy.cfg
├── README.md
└── news/
    ├── items.py          # Data model (NewsItem)
    ├── lib.py            # Date parsing utilities
    ├── pipelines.py      # MongoDB & Elasticsearch logic
    ├── settings.py       # Rate limits & pipeline config
    └── spiders/
        ├── base_rss.py   # Reusable RSS spider class
        ├── antara.py     # ...and 11 other spiders
```

---

## ⚙️ Installation

### Prerequisites

- Python 3.11 or higher
- MongoDB (optional; disabled by default)
- Elasticsearch (optional)

### Steps

```bash
# Clone the repository
git clone <repo-url>
cd news

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Usage

```bash
# Activate virtual environment
source .venv/bin/activate

# Run a spider and overwrite its JSON output
scrapy crawl antara -O scraped_data/antara.json
scrapy crawl detik -O scraped_data/detik.json
```

---

## 📦 Data Model (`NewsItem`)

| Field | Type | Description | Available In |
|---|---|---|---|
| `title` | string | Article headline | All |
| `link` | string | Article canonical URL | All |
| `date_post` | datetime | Publication date (UTC) | All |
| `date_post_local_time`| string | Publication date (local string) | All |
| `source` | string | Spider name (e.g., 'detik') | All |
| `author` | string | Author name | Scraper + some RSS |
| `tags` | list | Publisher topic tags; empty when unavailable | All |
| `summary` | string | Short excerpt (max 500 chars)| RSS + structured HTML |
| `image_url` | string | Thumbnail image URL | RSS + structured HTML |

---

## 🔧 Configuration (`settings.py`)

All core settings are in `news/settings.py`. Pipelines are configured as follows:

```python
# MongoDB and Elasticsearch pipelines are optional and disabled by default.
```

All spiders use a rolling 24-hour window by default. This means "the latest
24 hours from crawl start," not only articles published after midnight:

```python
NEWS_LOOKBACK_HOURS = 24
```

Override it for one crawl with `-s NEWS_LOOKBACK_HOURS=12`.

- Use `scrapy crawl <spider> -O scraped_data/<spider>.json` for local JSON.
- When enabled, **MongoDB** creates collections based on the source (e.g., `antara-news`, `detik-news`).
- **Deduplication** is handled natively in both pipelines using the `link` field.

---

## 📄 License

This project is for **educational and research purposes only**.
Users are responsible for ensuring their use complies with applicable laws and the Terms of Service of any website they interact with.
