# 📰 News Scraper

A web scraping framework built with [Scrapy](https://scrapy.org/) for collecting news articles from Indonesian news portals. Built for **educational and research purposes only**.

> ⚠️ **Disclaimer**: This project is intended for educational purposes only. Always respect the Terms of Service of any website you interact with. The author is not responsible for any misuse of this tool.

---

## 🚀 Features

- Scrapes article metadata (title, author, date, tags, URL) from multiple news sources
- Supports multiple storage backends: **Elasticsearch** and **MongoDB**
- Rotating User-Agent via `scrapy-fake-useragent`
- Duplicate URL filtering
- Easily extensible with new spiders

---

## 🗂️ Project Structure

```
.
├── requirements.txt
├── scrapy.cfg
├── README.md
└── news/
    ├── items.py          # Data model
    ├── lib.py            # Utility functions
    ├── middlewares.py    # Custom middlewares
    ├── pipelines.py      # Storage pipelines
    ├── settings.py       # Project configuration
    └── spiders/          # Spider collection
```

---

## ⚙️ Installation

### Prerequisites

- Python 3.11 or higher
- pip

### Steps

```bash
# Clone the repository
git clone <repo-url>
cd news

# Create virtual environment
python3 -m venv news-venv
source news-venv/bin/activate  # Linux/Mac
# news-venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 🔧 Configuration

All settings are managed in `news/settings.py`.

### Elasticsearch Pipeline

```python
ITEM_PIPELINES = {
    'news.pipelines.ElasticSearchPipeline': 300,
}

ELASTICSEARCH_HOSTS = 'localhost'
ELASTICSEARCH_PORT = 9200
ELASTICSEARCH_INDEX = 'news'
ELASTICSEARCH_UNIQ_KEY = 'link'
ELASTICSEARCH_TYPE = '_doc'
```

### MongoDB Pipeline

Install the extra dependency first:

```bash
pip install pymongo
```

```python
ITEM_PIPELINES = {
    'news.pipelines.NewsPipeline': 200,
}

MONGO_URI = 'mongodb://localhost:27017'
MONGO_DB = 'news'
```

### Output to File Only (no pipeline)

```python
ITEM_PIPELINES = {}
```

---

## 🚀 Usage

```bash
# Activate virtual environment
source news-venv/bin/activate

# Run a spider and save to JSON
scrapy crawl <spider_name> -o output.json

# Run a spider without saving to file (pipeline only)
scrapy crawl <spider_name>
```

---

## 📦 Data Model

Each scraped item contains the following fields:

| Field | Type | Description |
|---|---|---|
| `title` | string | Article headline |
| `author` | string | Author name |
| `date_post` | datetime | Publication date (UTC) |
| `date_post_local_time` | string | Publication date (local time) |
| `link` | string | Article URL |
| `tags` | list | Article tags |
| `source` | string | Spider name / news source |

---

## 🛠️ Tech Stack

| Package | Version | Purpose |
|---|---|---|
| Scrapy | 2.15.1+ | Core scraping framework |
| Twisted | 25.5.0+ | Async networking |
| lxml | 6.1.0+ | HTML/XML parsing |
| elasticsearch | 9.x+ | Elasticsearch client |
| scrapy-fake-useragent | 1.4.4 | User-Agent rotation |
| tldextract | 3.3.1+ | Domain extraction |

---

## 📄 License

This project is for **educational and research purposes only**.
Users are responsible for ensuring their use complies with applicable laws and the Terms of Service of any website they interact with.
