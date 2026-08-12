# -*- coding: utf-8 -*-
"""Detik news spider backed by Detik's public RSS feed."""

import asyncio

import requests
import scrapy
from scrapy.http import XmlResponse

from news.spiders.base_rss import RSSBaseSpider


class DetikSpider(RSSBaseSpider):
    name = 'detik'
    source = 'detik'
    rss_url = [
        {'url': 'https://news.detik.com/rss', 'category': 'Berita'},
        {'url': 'https://finance.detik.com/rss', 'category': 'Finance'},
        {'url': 'https://hot.detik.com/rss', 'category': 'Hiburan'},
        {'url': 'https://sport.detik.com/rss', 'category': 'Sport'},
        {'url': 'https://inet.detik.com/rss', 'category': 'Teknologi'},
        {'url': 'https://oto.detik.com/rss', 'category': 'Otomotif'},
        {'url': 'https://travel.detik.com/rss', 'category': 'Travel'},
        {'url': 'https://food.detik.com/rss', 'category': 'Kuliner'},
        {'url': 'https://health.detik.com/rss', 'category': 'Kesehatan'},
        {'url': 'https://wolipop.detik.com/rss', 'category': 'Lifestyle'},
    ]

    async def start(self):
        """Fetch feeds through requests when Detik stalls Scrapy HTTP."""
        results = await asyncio.gather(
            *(self.fetch_feed(feed) for feed in self.rss_url),
            return_exceptions=True,
        )
        for feed, result in zip(self.rss_url, results):
            if isinstance(result, Exception):
                self.logger.error(
                    'Unable to fetch Detik feed %s: %s',
                    feed['url'],
                    result,
                )
                continue
            for item in result:
                yield item

    async def fetch_feed(self, feed):
        url = feed['url']
        headers = {
            'User-Agent': self.settings.get('USER_AGENT'),
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        }

        for attempt in range(3):
            try:
                response = await asyncio.to_thread(
                    requests.get,
                    url,
                    headers=headers,
                    timeout=(10, 60),
                )
                response.raise_for_status()
                break
            except requests.RequestException:
                if attempt == 2:
                    raise
                await asyncio.sleep(attempt + 1)

        request = scrapy.Request(
            url=url,
            headers=headers,
            meta={'feed_category': feed['category']},
        )
        rss_response = XmlResponse(
            url=url,
            body=response.content,
            encoding=response.encoding or 'utf-8',
            request=request,
        )
        return list(self.parse(rss_response))
