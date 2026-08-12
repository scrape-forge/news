# -*- coding: utf-8 -*-
"""Suara spider using its public all-category news sitemaps."""

from datetime import timezone
from urllib.parse import urlparse

import scrapy

from news.items import NewsItem
from news.spiders.structured_data import (
    extract_article_data,
    iter_news_sitemap_entries,
    iter_sitemap_locations,
)
from news.spiders.time_window import LOCAL_TZ, RecentWindowMixin


class SuaraSpider(RecentWindowMixin, scrapy.Spider):
    name = 'suara'
    allowed_domains = ['www.suara.com']

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'DOWNLOAD_TIMEOUT': 60,
        'RETRY_TIMES': 2,
        'DOWNLOADER_MIDDLEWARES': {},
    }

    async def start(self):
        yield scrapy.Request(
            url='https://www.suara.com/sitemap.xml',
            callback=self.parse,
        )

    def parse(self, response):
        requested_category = getattr(self, 'category', None)
        for sitemap in iter_sitemap_locations(response):
            url = sitemap['url'] or ''
            if not url.endswith('/sitemap-news.xml'):
                continue
            if requested_category:
                sitemap_category = urlparse(url).path.strip('/').split('/')[0]
                if sitemap_category != requested_category:
                    continue
            yield scrapy.Request(url=url, callback=self.parse_sitemap)

    def parse_sitemap(self, response):
        for entry in iter_news_sitemap_entries(response):
            if entry['url'] and self.is_in_window(entry['published_at']):
                yield scrapy.Request(
                    url=entry['url'],
                    callback=self.parse_detail,
                    cb_kwargs={'sitemap_data': entry},
                )

    def parse_detail(self, response, sitemap_data):
        data = extract_article_data(response)
        published_at = data['published_at'] or sitemap_data['published_at']
        if not self.is_in_window(published_at):
            return

        path_category = urlparse(response.url).path.strip('/').split('/')[0]
        category = data['category'] or path_category.replace('-', ' ').title()

        item = NewsItem()
        item['date_post'] = published_at.astimezone(timezone.utc)
        local_time = published_at.astimezone(LOCAL_TZ)
        item['date_post_local_time'] = local_time.strftime('%d-%m-%Y %H:%M')
        item['author'] = data['author']
        item['title'] = data['title'] or sitemap_data['title']
        item['link'] = response.url
        item['category'] = category
        item['tags'] = data['tags'] or sitemap_data['tags']
        item['source'] = self.name
        item['summary'] = data['summary'][:500] if data['summary'] else None
        item['image_url'] = data['image_url'] or sitemap_data['image_url']
        yield item
