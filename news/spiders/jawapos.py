# -*- coding: utf-8 -*-
"""Jawapos spider using its public recent-post sitemap and article pages."""

from datetime import timezone
from urllib.parse import urlparse

import scrapy

from news.items import NewsItem
from news.spiders.structured_data import (
    extract_article_data,
    iter_news_sitemap_entries,
)
from news.spiders.time_window import LOCAL_TZ, RecentWindowMixin


class JawaposSpider(RecentWindowMixin, scrapy.Spider):
    name = 'jawapos'
    allowed_domains = ['jawapos.com', 'www.jawapos.com']

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'DOWNLOADER_MIDDLEWARES': {},
    }

    async def start(self):
        yield scrapy.Request(
            url='https://www.jawapos.com/post-recent.xml',
            callback=self.parse_sitemap,
        )

    def parse_sitemap(self, response):
        for entry in iter_news_sitemap_entries(response):
            published_at = entry['published_at']
            if published_at is None or not entry['url']:
                continue

            # Jawapos labels local wall-clock sitemap times with "Z". Treat
            # that value as WIB for discovery, then verify the article's
            # correctly zoned date on its detail page.
            sitemap_local = LOCAL_TZ.localize(
                published_at.replace(tzinfo=None)
            ).astimezone(timezone.utc)
            if not self.is_in_window(sitemap_local):
                continue
            yield scrapy.Request(
                url=entry['url'],
                callback=self.parse_detail,
                cb_kwargs={'sitemap_data': entry},
            )

    def parse_detail(self, response, sitemap_data):
        data = extract_article_data(response)
        published_at = data['published_at']
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
