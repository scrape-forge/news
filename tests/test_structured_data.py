from unittest import TestCase

from scrapy.http import XmlResponse

from news.spiders.structured_data import (
    iter_news_sitemap_entries,
    iter_sitemap_locations,
)


class SitemapParserTests(TestCase):
    @staticmethod
    def response(body):
        return XmlResponse(
            url='https://example.com/sitemap.xml',
            body=body.encode(),
            encoding='utf-8',
        )

    def test_parses_sitemap_index(self):
        response = self.response(
            '''
            <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
              <sitemap>
                <loc>https://example.com/news.xml</loc>
                <lastmod>2026-08-12T10:00:00+07:00</lastmod>
              </sitemap>
            </sitemapindex>
            '''
        )

        location = next(iter_sitemap_locations(response))

        self.assertEqual(location['url'], 'https://example.com/news.xml')
        utc_offset = location['modified_at'].utcoffset().total_seconds()
        self.assertEqual(utc_offset, 25200)

    def test_parses_namespaced_news_entry(self):
        response = self.response(
            '''
            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
                    xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"
                    xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
              <url>
                <loc>https://example.com/category/article</loc>
                <news:news>
                  <news:publication_date>2026-08-12T10:00:00+07:00</news:publication_date>
                  <news:title>Recent article</news:title>
                  <news:keywords>News, Indonesia</news:keywords>
                </news:news>
                <image:image>
                  <image:loc>https://example.com/image.jpg</image:loc>
                </image:image>
              </url>
            </urlset>
            '''
        )

        entry = next(iter_news_sitemap_entries(response))

        self.assertEqual(entry['title'], 'Recent article')
        self.assertEqual(entry['tags'], ['News', 'Indonesia'])
        self.assertEqual(entry['image_url'], 'https://example.com/image.jpg')
        utc_offset = entry['published_at'].utcoffset().total_seconds()
        self.assertEqual(utc_offset, 25200)
