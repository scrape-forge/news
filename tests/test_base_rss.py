from datetime import datetime, timedelta, timezone
from unittest import TestCase

from scrapy import Request
from scrapy.http import XmlResponse

from news.spiders.base_rss import RSSBaseSpider


class _RSSSpider(RSSBaseSpider):
    name = 'test_rss'
    rss_url = 'https://example.com/rss'

    @property
    def lookback_hours(self):
        return 24


class RSSBaseSpiderTests(TestCase):
    def setUp(self):
        self.spider = _RSSSpider()
        end = datetime(2026, 8, 12, 5, tzinfo=timezone.utc)
        self.spider._window_end_utc = end
        self.spider._window_start_utc = end - timedelta(hours=24)

    @staticmethod
    def response():
        body = b'''
        <rss><channel><item>
          <title>Recent article</title>
          <link>https://example.com/article</link>
          <pubDate>Wed, 12 Aug 2026 11:00:00 +0700</pubDate>
          <description>Article summary</description>
        </item></channel></rss>
        '''
        request = Request(
            'https://example.com/rss',
            meta={'feed_category': 'News'},
        )
        return XmlResponse(
            url=request.url,
            request=request,
            body=body,
            encoding='utf-8',
        )

    def test_does_not_use_category_as_a_tag(self):
        item = list(self.spider.parse(self.response()))[0]

        self.assertEqual(item['category'], 'General')
        self.assertEqual(item['tags'], [])

    def test_keeps_topic_tags_distinct_from_category(self):
        response = self.response()
        response._set_body(
            response.body.replace(
                b'<description>',
                b'<category>News</category>'
                b'<category>Flood</category>'
                b'<category>Jakarta</category><description>',
            )
        )

        item = list(self.spider.parse(response))[0]

        self.assertEqual(item['category'], 'General')
        self.assertEqual(item['tags'], ['Flood', 'Jakarta'])


    def test_deduplicates_link_across_feed_responses(self):
        first_items = list(self.spider.parse(self.response()))
        second_items = list(self.spider.parse(self.response()))

        self.assertEqual(len(first_items), 1)
        self.assertEqual(second_items, [])
