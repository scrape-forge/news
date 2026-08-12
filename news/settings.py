# -*- coding: utf-8 -*-

# Scrapy settings for news project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html
#
# v2.0 changes:
#   - ROBOTSTXT_OBEY = True (compliance)
#   - DOWNLOAD_DELAY = 2 (rate limiting)
#   - AUTOTHROTTLE enabled
#   - RandomUserAgentMiddleware enabled
#   - ITEM_PIPELINES enabled (MongoDB by default)
#   - Both pipelines now handle all 12 sources

BOT_NAME = 'news'

# Every spider emits articles from this rolling window only.
NEWS_LOOKBACK_HOURS = 24

SPIDER_MODULES = ['news.spiders']
NEWSPIDER_MODULE = 'news.spiders'

# Obey robots.txt rules — enabled for legal compliance (v2.0)
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1  # Be a good citizen per domain

# Configure a delay for requests — required for compliance (v2.0)
# RSS spiders override this because they only request public feed endpoints.
DOWNLOAD_DELAY = 2

# Disable cookies (not needed for news scraping)
COOKIES_ENABLED = False

# Disable Telnet Console
TELNETCONSOLE_ENABLED = False

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id,en;q=0.5',
}

# Enable downloader middlewares — User-Agent rotation enabled (v2.0)
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
    'scrapy_fake_useragent.middleware.RetryUserAgentMiddleware': 401,
}

# Fake user-agent provider chain
FAKEUSERAGENT_PROVIDERS = [
    'scrapy_fake_useragent.providers.FakeUserAgentProvider',
    'scrapy_fake_useragent.providers.FakerProvider',
    'scrapy_fake_useragent.providers.FixedUserAgentProvider',
]
USER_AGENT = 'Mozilla/5.0 (compatible; NewsScraper/2.0; +https://github.com/)'

# Optional database pipelines. Enable these only when their services are
# available. Use Scrapy's `-O` option for local JSON export.
import os

# --- PostgreSQL ---
POSTGRES_HOST = os.getenv('POSTGRES_HOST', '')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
POSTGRES_DB = os.getenv('POSTGRES_DB', 'news_db')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')

# Allowed Master Categories to persist. If empty, all categories are kept.
ALLOWED_CATEGORIES = os.getenv(
    'ALLOWED_CATEGORIES',
    'Ekonomi & Bisnis,Politik & Hukum,Teknologi & Sains'
)

ITEM_PIPELINES = {
    'news.pipelines.CategoryFilterPipeline': 100,
    # 'news.pipelines.NewsPipeline': 300,
    # 'news.pipelines.ElasticSearchPipeline': 500,
}

if POSTGRES_HOST or os.getenv('ENABLE_POSTGRES_PIPELINE', '').lower() in ('true', '1'):
    ITEM_PIPELINES['news.pipelines.PostgresPipeline'] = 400


# --- MongoDB ---
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.getenv('MONGO_DB', 'news')

# --- Elasticsearch ---
ELASTICSEARCH_HOSTS = os.getenv('ELASTICSEARCH_HOSTS', 'localhost')
ELASTICSEARCH_PORT = os.getenv('ELASTICSEARCH_PORT', '9200')
ELASTICSEARCH_INDEX = os.getenv('ELASTICSEARCH_INDEX', 'news')
ELASTICSEARCH_USERNAME = os.getenv('ELASTICSEARCH_USERNAME', '')
ELASTICSEARCH_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD', '')
ELASTICSEARCH_TYPE = '_doc'
ELASTICSEARCH_UNIQ_KEY = 'link'  # fixed: was 'url', item field is 'link'


# Enable and configure the AutoThrottle extension (v2.0)
# Automatically adjusts download delay based on server response times
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1     # Initial download delay (seconds)
AUTOTHROTTLE_MAX_DELAY = 10      # Maximum delay in case of high latencies
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0  # Avg requests in parallel per server
AUTOTHROTTLE_DEBUG = False

# Enable HTTP caching (optional — useful during development to avoid re-fetching)
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 3600
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504]
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
