# 📰 News Scraper v2.0

A hybrid RSS and web scraping framework built with [Scrapy](https://scrapy.org/) for collecting news articles from Indonesian news portals. Built for **educational and research purposes only**.

> ⚠️ **Disclaimer**: This project is intended for educational purposes only. Always respect the Terms of Service of any website you interact with. The author is not responsible for any misuse of this tool.

---

## 🚀 Features (v2.0)

- **Hybrid Architecture (Legal & Stable)**: Uses official RSS feeds for 6 sources, falling back to rate-limited scrapers for the remaining 6.
- **Compliance First**: `ROBOTSTXT_OBEY` enabled, dynamic download delays (`AUTOTHROTTLE`), and domain concurrency limits.
- **Enriched Data**: Extracts `image_url` and `summary` (excerpts) natively from RSS feeds.
- **Unified Pipelines**: MongoDB and Elasticsearch pipelines that handle all 12 spiders with built-in deduplication.
- **Rotating User-Agent**: Built-in via `scrapy-fake-useragent`.

---

## 🕷️ Supported Sources

**Group A: RSS-based (Fully legal, richer data)**
- `antara`, `tribun`, `sindo`, `republika`, `jawapos`, `okezone`

**Group B: HTML Scrapers (Rate-limited, robots.txt compliant)**
- `detik`, `kompas`, `liputan6`, `merdeka`, `tempo`, `suara`

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
- MongoDB (optional, enabled by default)
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

# Run a spider and save to JSON
scrapy crawl antara -o output.json

# Run a spider directly into MongoDB (default pipeline)
scrapy crawl detik
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
| `tags` | list | Article categories/tags | Scraper + some RSS |
| `summary` | string | Short excerpt (max 500 chars)| **RSS Only** |
| `image_url` | string | Thumbnail image URL | **RSS Only** |

---

## 🔧 Configuration (`settings.py`)

All core settings are in `news/settings.py`. Pipelines are configured as follows:

```python
ITEM_PIPELINES = {
    'news.pipelines.NewsPipeline': 300,            # MongoDB (Enabled)
    # 'news.pipelines.ElasticSearchPipeline': 500, # ES (Disabled by default)
}
```

- **MongoDB** will auto-create collections based on the source (e.g., `antara-news`, `detik-news`).
- **Deduplication** is handled natively in both pipelines using the `link` field.

---

## 📄 License

This project is for **educational and research purposes only**.
Users are responsible for ensuring their use complies with applicable laws and the Terms of Service of any website they interact with.
