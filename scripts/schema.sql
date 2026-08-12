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
    crawled_at TIMESTAMPTZ DEFAULT NOW()        -- Timestamp when fetched by scraper
);

-- 2. Performance Indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_news_link ON news_articles (link);
CREATE INDEX IF NOT EXISTS idx_news_source_date ON news_articles (source, date_post DESC);
CREATE INDEX IF NOT EXISTS idx_news_date_post ON news_articles (date_post DESC);
CREATE INDEX IF NOT EXISTS idx_news_category ON news_articles (category);
CREATE INDEX IF NOT EXISTS idx_news_tags_gin ON news_articles USING GIN (tags);

-- 3. Full-Text Search Index (Optional: Fast keyword searching on title & summary)
CREATE INDEX IF NOT EXISTS idx_news_fts ON news_articles 
USING gin (to_tsvector('simple', title || ' ' || COALESCE(summary, '')));
