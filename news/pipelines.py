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

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        spider.logger.info(f'MongoDB connected: {self.mongo_uri} / db={self.mongo_db}')

    def close_spider(self, spider):
        self.client.close()
        spider.logger.info('MongoDB connection closed.')

    def process_item(self, item, spider):
        # Derive collection name from source field (e.g. 'antara' → 'antara-news')
        source = item.get('source', spider.name)
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

    def open_spider(self, spider):
        self.es = Elasticsearch(hosts=self.es_uri)
        spider.logger.info(f'Elasticsearch connected: {self.es_uri} / index={self.es_index}')

    def close_spider(self, spider):
        if self.es:
            self.es.close()
        spider.logger.info('Elasticsearch connection closed.')

    def process_item(self, item, spider):
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