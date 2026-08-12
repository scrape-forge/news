# 📋 Product Requirement Document (PRD) & Goals Specification
# PAPAGON INSIGHT: Indonesian News Data & Intelligence Platform

**Document Version:** 2.0  
**Status:** APPROVED & LOCKED  
**Brand Name:** PAPAGON INSIGHT  
**Target Environment:** Linux VPS (1.89 GB RAM, 2 CPU Cores, Docker 29.6.1, PostgreSQL 16)  
**Budget Constraint:** $0.00 (Zero paid API subscriptions)

---

## 1. Executive Summary & Vision

### 1.1 Purpose
**PAPAGON INSIGHT** is an automated, data-driven Indonesian news intelligence platform designed to scrape, clean, enrich, and analyze real-time headlines across 12 major Indonesian news portals. Inspired by the data density and precision of the Bloomberg Terminal, PAPAGON INSIGHT translates raw unstructured news into structured market intelligence.

### 1.2 Core Product Goals (The 4 Fundamental Questions)
The platform directly answers 4 fundamental intelligence goals:
1. **Goal 1: "What happened now?"** ➔ Real-time multi-portal headline stream (scraped every 6 hours across 12 portals).
2. **Goal 2: "What is the biggest issue now?"** ➔ Major Story Clustering Engine that aggregates breaking stories across multiple publishers by article volume.
3. **Goal 3: "What is the trend now?"** ➔ High-speed GIN-indexed Tag Cloud showing trending keywords and emerging topics.
4. **Goal 4: "What happened in economy based on data?"** ➔ Macroeconomic Sentiment Scores (-1.0 to +1.0), Sector Heatmaps, and AI-generated Executive Summaries.

---

## 2. System Architecture & Component Design

```mermaid
graph TD
    subgraph 1. Ingestion Layer (Scrapy)
        A1[Group A: 8 RSS Spiders] --> B1[Clean & Normalize Engine]
        A2[Group B: 4 Sitemap Spiders] --> B1
        B1 -->|Filter ALLOWED_CATEGORIES| B2[CategoryFilterPipeline]
    end

    subgraph 2. Ingestion Storage (PostgreSQL)
        B2 -->|Upsert ON CONFLICT link| C[(PostgreSQL: news_articles)]
    end

    subgraph 3. Asynchronous AI Enrichment (Cron Worker)
        C -->|Fetch Un-enriched Items| D1[tag_worker.py - Hit-and-Run]
        D1 -->|1 Batch Call per Min| D2[Groq Free API: llama-3.1-8b-instant]
        D2 -->|Return: Tags, Sentiment, Bullets, Entities, Sector| D1
        D1 -->|Check rem_tpm < 1500 Safeguard| D3[Batch UPDATE SQL]
        D3 --> C
    end

    subgraph 4. User Interface (PAPAGON INSIGHT Dashboard)
        C -->|GIN Index Query < 1ms| E1[Live News Stream - Goal 1]
        C -->|Tag Cloud Aggregation| E2[Trending Topic Cloud - Goal 3]
        C -->|Sentiment & Sector Aggregation| E3[Economic Sentiment Gauge - Goal 4]
        C -->|Story Clustering| E4[Major Issue Clusters - Goal 2]
    end
```

---

## 3. Data Ingestion & Categorization Standard

### 3.1 10 Master Category Taxonomy
Raw scraped categories across 78 portal variations are automatically mapped to **10 Master Categories** during ingestion:

| Master Category | Mapped Raw Categories | Persisted to DB? |
|---|---|---|
| 💼 **Ekonomi & Bisnis** | `Ekonomi`, `Economy`, `Ekonomi Bisnis`, `Bisnis`, `Finance`, `Finansial`, `Market Update`, `Energi`, `Kripto` | ✅ YES (Primary) |
| 🏛️ **Politik & Hukum** | `Politik`, `Nasional`, `Kilas-Kementerian`, `Kasuistika` | ✅ YES (Primary) |
| ⚡ **Teknologi & Sains** | `Teknologi`, `Tekno`, `Techno`, `Sains` | ✅ YES (Primary) |
| 🌐 **Internasional** | `International`, `Internasional`, `Dunia` | ⚪ Optional |
| ⚽ **Olahraga** | `Sport`, `Bola`, `Sepak Bola Dunia`, `Liga Champion`, `MotoGP` | 🔴 Dropped by Filter |
| 🗺️ **Regional & Daerah** | `Regional`, `Berita Daerah`, `Daerah`, `Megapolitan`, `Metro` | ⚪ Optional |
| 🏥 **Kesehatan** | `Kesehatan`, `Health` | ⚪ Optional |
| 🌿 **Gaya Hidup & Edukasi**| `Lifestyle`, `Fashion`, `Beauty`, `Food`, `Kuliner`, `Travel`, `Edukasi` | 🔴 Dropped by Filter |
| 🎬 **Hiburan & Seleb** | `Entertainment`, `ShowBiz`, `Seleb`, `Hiburan`, `Hot Gossip` | 🔴 Dropped by Filter |
| 🕌 **Religi & Humaniora** | `Islam Digest`, `Islam Nusantara`, `Ihram`, `Filantropi Khazanah` | 🔴 Dropped by Filter |

### 3.2 Ingestion Category Filtering
To preserve storage and focus strictly on valuable intelligence, `CategoryFilterPipeline` enforces `ALLOWED_CATEGORIES` in `.env`:

```env
ALLOWED_CATEGORIES="Ekonomi & Bisnis,Politik & Hukum,Teknologi & Sains"
```
Articles outside these allowed categories are dropped prior to database insertion.

---

## 4. Groq AI Data Enrichment Specification

### 4.1 AI Worker Execution Flow (`scripts/tag_worker.py`)
- **Execution Model**: Asynchronous, cron-triggered Hit-and-Run script (`*/1 * * * *`).
- **Model**: Groq Cloud Free Tier `llama-3.1-8b-instant`.
- **Batching**: 10 to 15 articles per single API request.
- **Execution Speed**: Zero artificial `time.sleep()` delays; operates at full speed until quota threshold.

### 4.2 Single Request Payload & Response Schema
In 1 single API call per batch, Groq returns:

```json
{
  "101": {
    "tags": ["Suku Bunga BI", "Bank Indonesia", "Ekonomi"],
    "sentiment": 0.45,
    "sentiment_label": "Positive",
    "bullets": [
      "Bank Indonesia menahan suku bunga acuan BI Rate pada level 6,25%.",
      "Keputusan diambil untuk menjaga stabilitas nilai tukar Rupiah terhadap Dolar AS."
    ],
    "entities": {
      "companies": ["Bank Indonesia"],
      "people": ["Perry Warjiyo"],
      "locations": ["Jakarta"]
    },
    "sector": "Banking & Finance"
  }
}
```

### 4.3 Proactive Rate Limit Safeguard (HTTP 429 Prevention)
Groq Free Tier enforces **6,000 Tokens Per Minute (TPM)** and **30 Requests Per Minute (RPM)**.
- **Header Inspection**: Inspects `x-ratelimit-remaining-tokens` and `x-ratelimit-remaining-requests` after every call.
- **Halting Threshold**: If `rem_tpm < 1500` (25% cushion) or `rem_rpm < 2`, the worker immediately halts further requests in that run and exits cleanly (`exit 0`).
- **Result**: **0% HTTP 429 rate limit errors**.

---

## 5. PostgreSQL Database Schema & Indexing

### 5.1 Table DDL (`news_articles`)

```sql
CREATE TABLE IF NOT EXISTS news_articles (
    id BIGSERIAL PRIMARY KEY,
    link TEXT UNIQUE NOT NULL,                  -- Canonical article URL (deduplication key)
    source VARCHAR(50) NOT NULL,                -- Spider source name (e.g. 'detik', 'antara')
    title TEXT NOT NULL,                        -- Headline (cleaned)
    author TEXT,                                -- Author name
    category VARCHAR(100),                      -- Master Category
    tags TEXT[] DEFAULT '{}',                   -- Standardized topic tags
    date_post TIMESTAMPTZ NOT NULL,             -- Publication date in UTC
    date_post_local VARCHAR(25),                -- Local time string (WIB)
    summary TEXT,                               -- Article summary
    image_url TEXT,                             -- Thumbnail URL
    crawled_at TIMESTAMPTZ DEFAULT NOW(),       -- Scraping timestamp
    
    -- AI Enrichment Fields
    sentiment_score FLOAT,                      -- -1.0 (Negative) to +1.0 (Positive)
    sentiment_label VARCHAR(20),                -- 'Positive', 'Negative', 'Neutral'
    ai_bullets TEXT[],                          -- 2-bullet executive summary
    entities JSONB,                             -- Extracted companies, people, locations
    sector VARCHAR(50)                          -- Industry sector classification
);
```

### 5.2 Performance Indexing Strategy
- **`idx_news_link`**: Unique B-Tree index on `link` (Upsert key).
- **`idx_news_tags_gin`**: **GIN Index on `tags` (`USING GIN (tags)`)** for sub-millisecond tag cloud aggregation.
- **`idx_news_fts`**: **GIN Full-Text Search Index** on `title || ' ' || summary`.
- **`idx_news_category_date`**: B-Tree index on `(category, date_post DESC)` for fast category feeds.
- **`idx_news_entities_gin`**: GIN index on `entities` (JSONB) for stock ticker/company searches.

---

## 6. Dashboard Interface Specifications (Bloomberg Terminal Style)

### 6.1 Design Aesthetics
- **Theme**: Dark mode glassmorphism (`#0B0E14` background, `#1A1F2C` cards, `#00F2FE` cyan highlights).
- **Typography**: `Inter` / `JetBrains Mono` for financial data clarity.

### 6.2 Key UI Components
1. **Live Intelligence Feed (Goal 1)**: Streaming headline list with source badges, master category pills, and 2-bullet AI summaries.
2. **Major Issue Clusters (Goal 2)**: Aggregated breaking story clusters grouped across publishers.
3. **Trending Topic Cloud (Goal 3)**: Interactive GIN-aggregated tag cloud weighted by frequency.
4. **Macro Economic Sentiment Gauge & Sector Heatmap (Goal 4)**: Live gauge showing overall Indonesian market confidence score (-1.0 to +1.0).

---

## 7. Performance & Resource Footprint

| Component | RAM Usage | CPU Usage | Execution Time |
|---|---|---|---|
| **Scrapy Spiders (12 Portals)** | ~80 MB | ~15% (during crawl) | ~30s per 6h cycle |
| **Python Rule Normalizer (`lib.py`)** | ~0 MB | < 0.1% | < 0.01ms / item |
| **Groq AI Tag Worker (`tag_worker.py`)** | ~15 MB | < 1.0% | ~1.2s / batch |
| **PostgreSQL Database Engine** | ~120 MB | < 2.0% | < 1ms / query |
| **Total VPS Footprint** | **~215 MB RAM** | **Minimal** | **Leaves 1.6 GB RAM Free** |

---

## 8. Implementation Checklist

- [x] Multi-stage Dockerfile (`dev` and `prod` targets).
- [x] Multi-portal Scrapy spiders (Group A RSS & Group B Sitemap).
- [x] PostgreSQL pipeline with upsert deduplication logic.
- [x] 10 Master Category Taxonomy mapping (`normalize_category`).
- [x] Category Filter Pipeline (`CategoryFilterPipeline`).
- [x] Hit-and-Run Groq AI Tag Worker (`scripts/tag_worker.py`).
- [x] Proactive TPM Safety Check (`rem_tpm < 1500`).
- [x] GIN indexes on `tags` and Full-Text Search.
- [ ] Schema update migration for AI enrichment fields (`sentiment_score`, `ai_bullets`, `entities`, `sector`).
