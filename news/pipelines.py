# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import hashlib
import pymongo
from elasticsearch import Elasticsearch

class NewsPipeline(object):
    detik_collection = 'detik-news'
    kompas_collection = 'kompas-news'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        if spider.name == 'detik':
            self.db[self.detik_collection].insert_one(dict(item))
        elif spider.name == 'kompas':
            self.db[self.kompas_collection].insert_one(dict(item))
        return item

class ElasticSearchPipeline(object):
    def __init__(self, es_hosts, es_port, es_index, es_unique_key, es_type):
        self.es_uri = "http://{hosts}:{port}".format(hosts=es_hosts, port=es_port)
        self.es_index = es_index
        self.es_unique_key = es_unique_key
        self.es_type = es_type
        self.es = Elasticsearch(hosts=self.es_uri)
        print("URI:", self.es_uri)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            es_hosts=crawler.settings.get('ELASTICSEARCH_HOSTS'),
            es_port=crawler.settings.get('ELASTICSEARCH_PORT'),
            es_index=crawler.settings.get('ELASTICSEARCH_INDEX'),
            es_unique_key=crawler.settings.get('ELASTICSEARCH_UNIQ_KEY'),
            es_type=crawler.settings.get('ELASTICSEARCH_TYPE'),
        )

    def process_item(self, item, spider):
        unique_id = self._get_item_key(item)
        print('UNIQUE_ID', unique_id)
        self.es.index(
            index=self.es_index,
            document=dict(item),
            id=unique_id
        )
        return item

    def _get_item_key(self, item):
        value = str(item['link']).encode('utf-8')
        return hashlib.sha1(value).hexdigest()