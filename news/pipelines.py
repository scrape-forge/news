# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
#
# v2.0 changes:
#   - NewsPipeline: now handles ALL spiders (not just detik & kompas)
#   - NewsPipeline: uses upsert to prevent duplicate documents
#   - NewsPipeline: collection name derived dynamically from spider name
#   - ElasticSearchPipeline: added open_spider/close_spider lifecycle hooks
#   - ElasticSearchPipeline: fixed ELASTICSEARCH_UNIQ_KEY to use 'link'

import hashlib
import pymongo
from elasticsearch import Elasticsearch


class NewsPipeline:
    """
    MongoDB pipeline — stores items from ALL spiders.
    Collection name is derived from spider name: e.g. 'detik' → 'detik-news'
    Deduplicates by article URL using upsert.
    """

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB', 'news'),
        )

    def open_spider(self, spider=None):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider=None):
        self.client.close()

    def process_item(self, item, spider=None):
        # Derive collection name from source field (e.g. 'antara' → 'antara-news')
        source = item.get('source') or (spider.name if spider else 'unknown')
        collection_name = f'{source}-news'

        # Upsert by link — prevents duplicate documents on repeated crawls
        self.db[collection_name].update_one(
            {'link': item['link']},
            {'$set': dict(item)},
            upsert=True,
        )
        return item


class ElasticSearchPipeline:
    """
    Elasticsearch pipeline — indexes items from ALL spiders.
    Document ID is a SHA-1 hash of the article URL for deduplication.
    """

    def __init__(self, es_hosts, es_port, es_index, es_unique_key):
        self.es_uri = f'http://{es_hosts}:{es_port}'
        self.es_index = es_index
        self.es_unique_key = es_unique_key
        self.es = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            es_hosts=crawler.settings.get('ELASTICSEARCH_HOSTS'),
            es_port=crawler.settings.get('ELASTICSEARCH_PORT'),
            es_index=crawler.settings.get('ELASTICSEARCH_INDEX'),
            es_unique_key=crawler.settings.get('ELASTICSEARCH_UNIQ_KEY', 'link'),
        )

    def open_spider(self, spider=None):
        self.es = Elasticsearch(hosts=self.es_uri)

    def close_spider(self, spider=None):
        if self.es:
            self.es.close()

    def process_item(self, item, spider=None):
        unique_id = self._get_item_key(item)
        self.es.index(
            index=self.es_index,
            document=dict(item),
            id=unique_id,
        )
        return item

    def _get_item_key(self, item):
        """Generate a SHA-1 hash of the article URL for use as document ID."""
        value = str(item[self.es_unique_key]).encode('utf-8')
        return hashlib.sha1(value).hexdigest()


from scrapy.exceptions import DropItem


class CategoryFilterPipeline:
    """
    Filters out unwanted categories (e.g. Gossip, Sports, Entertainment).
    Only passes items matching ALLOWED_CATEGORIES configured in settings/env.
    """

    def __init__(self, allowed_categories=None):
        self.allowed_categories = allowed_categories or []

    @classmethod
    def from_crawler(cls, crawler):
        raw_allowed = crawler.settings.get('ALLOWED_CATEGORIES', '')
        if isinstance(raw_allowed, str):
            allowed = [cat.strip() for cat in raw_allowed.split(',') if cat.strip()]
        else:
            allowed = raw_allowed or []
        return cls(allowed_categories=allowed)

    def process_item(self, item, spider=None):
        if not self.allowed_categories:
            return item

        category = item.get('category')
        if not category or category not in self.allowed_categories:
            raise DropItem(f"Category '{category}' dropped (not in ALLOWED_CATEGORIES)")

        return item


class PostgresPipeline:

    """
    PostgreSQL pipeline — stores items from ALL spiders.
    Creates table automatically and uses UPSERT on article URL (link)
    to prevent duplicate records across crawls.
    """

    def __init__(self, host, port, dbname, user, password):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.conn = None
        self.cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            host=crawler.settings.get('POSTGRES_HOST'),
            port=crawler.settings.getint('POSTGRES_PORT'),
            dbname=crawler.settings.get('POSTGRES_DB'),
            user=crawler.settings.get('POSTGRES_USER'),
            password=crawler.settings.get('POSTGRES_PASSWORD'),
        )

    def open_spider(self, spider=None):
        import psycopg2

        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password,
        )
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_articles (
                id BIGSERIAL PRIMARY KEY,
                link TEXT UNIQUE NOT NULL,
                source VARCHAR(50) NOT NULL,
                title TEXT NOT NULL,
                author TEXT,
                category VARCHAR(100),
                tags TEXT[],
                date_post TIMESTAMPTZ NOT NULL,
                date_post_local VARCHAR(25),
                summary TEXT,
                image_url TEXT,
                crawled_at TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_news_source_date ON news_articles (source, date_post DESC);
            CREATE INDEX IF NOT EXISTS idx_news_date_post ON news_articles (date_post DESC);
        """)
        self.conn.commit()

    def close_spider(self, spider=None):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def process_item(self, item, spider=None):
        query = """
            INSERT INTO news_articles (
                link, source, title, author, category, tags,
                date_post, date_post_local, summary, image_url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (link) DO UPDATE SET
                title = EXCLUDED.title,
                category = COALESCE(EXCLUDED.category, news_articles.category),
                tags = EXCLUDED.tags,
                summary = COALESCE(EXCLUDED.summary, news_articles.summary),
                image_url = COALESCE(EXCLUDED.image_url, news_articles.image_url);
        """
        tags = item.get('tags')
        if isinstance(tags, str):
            tags = [tags]
        elif not tags:
            tags = []

        self.cursor.execute(
            query,
            (
                item.get('link'),
                item.get('source'),
                item.get('title'),
                item.get('author'),
                item.get('category'),
                tags,
                item.get('date_post'),
                item.get('date_post_local_time'),
                item.get('summary'),
                item.get('image_url'),
            ),
        )
        self.conn.commit()
        return item