-- ============================================================================
-- PostgreSQL Database Schema Migration for News Scraper v2.0
-- Project: scrape-forge/news
-- ============================================================================

-- 1. Create main news articles table
CREATE TABLE IF NOT EXISTS news_articles (
    id BIGSERIAL PRIMARY KEY,
    link TEXT UNIQUE NOT NULL,                  -- Canonical article URL (deduplication key)
    source VARCHAR(50) NOT NULL,                -- Spider source name (e.g. 'detik', 'antara')
    title TEXT NOT NULL,                        -- Headline
    author TEXT,                                -- Author name (nullable for RSS)
    category VARCHAR(100),                      -- Primary category/section
    tags TEXT[] DEFAULT '{}',                   -- List of tags/categories
    date_post TIMESTAMPTZ NOT NULL,             -- Publication date in UTC
    date_post_local VARCHAR(25),                -- WIB local string (DD-MM-YYYY HH:MM)
    summary TEXT,                               -- Short article excerpt (max 500 chars)
    image_url TEXT,                             -- Thumbnail image URL
    crawled_at TIMESTAMPTZ DEFAULT NOW(),       -- Timestamp when fetched by scraper
    sentiment_score DOUBLE PRECISION,
    sentiment_label VARCHAR(20),
    ai_bullets TEXT[],
    entities JSONB,
    sector VARCHAR(100),
    ai_enriched_at TIMESTAMPTZ
);

-- Upgrade existing installations without rebuilding the table.
ALTER TABLE news_articles
    ADD COLUMN IF NOT EXISTS sentiment_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS sentiment_label VARCHAR(20),
    ADD COLUMN IF NOT EXISTS ai_bullets TEXT[],
    ADD COLUMN IF NOT EXISTS entities JSONB,
    ADD COLUMN IF NOT EXISTS sector VARCHAR(100),
    ADD COLUMN IF NOT EXISTS ai_enriched_at TIMESTAMPTZ;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_news_sentiment_score'
    ) THEN
        ALTER TABLE news_articles
            ADD CONSTRAINT chk_news_sentiment_score
            CHECK (sentiment_score BETWEEN -1.0 AND 1.0);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_news_sentiment_label'
    ) THEN
        ALTER TABLE news_articles
            ADD CONSTRAINT chk_news_sentiment_label
            CHECK (sentiment_label IN ('Positive', 'Neutral', 'Negative'));
    END IF;
END
$$;

-- 2. Performance Indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_news_link ON news_articles (link);
CREATE INDEX IF NOT EXISTS idx_news_source_date ON news_articles (source, date_post DESC);
CREATE INDEX IF NOT EXISTS idx_news_date_post ON news_articles (date_post DESC);
CREATE INDEX IF NOT EXISTS idx_news_category ON news_articles (category);
CREATE INDEX IF NOT EXISTS idx_news_tags_gin ON news_articles USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_news_entities_gin ON news_articles USING GIN (entities);
CREATE INDEX IF NOT EXISTS idx_news_sector_date ON news_articles (sector, date_post DESC);
CREATE INDEX IF NOT EXISTS idx_news_ai_enriched_at ON news_articles (ai_enriched_at);

-- 3. Full-Text Search Index (Optional: Fast keyword searching on title & summary)
CREATE INDEX IF NOT EXISTS idx_news_fts ON news_articles 
USING gin (to_tsvector('simple', title || ' ' || COALESCE(summary, '')));
