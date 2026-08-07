# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
from news.lib import new_date_parse, remove_day, to_number_of_month
from news.items import NewsItem
from urllib.parse import urlparse, urlsplit, urlunsplit
class SuaraSpider(scrapy.Spider):
    name = 'suara'
    allowed_domains = ['www.suara.com']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
    }
    year = datetime.now().year
    start_urls = [       
        'https://www.suara.com/indeks/terkini/news/{}'.format(year),
        'https://www.suara.com/indeks/terkini/bisnis/{}'.format(year),
    ]

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

            
    def parse(self, response):
        detail_pages = response.css('.article-kanal-info a::attr(href)').getall()
        for page in detail_pages:
            yield scrapy.Request(page+'?page=all', callback=self.parse_detail)

        next_page = response.css('.pagination li.active +li')
        if next_page:
            parts = urlsplit(response.url)
            base_url = urlunsplit((parts.scheme, parts.netloc, parts.path, '', ''))
            page = base_url + next_page.css('::attr(href)').get()
            yield scrapy.Request(page, callback=self.parse)

    def parse_detail(self, response):
        part_url = urlparse(response.url)
        if part_url.netloc == self.allowed_domains[0]:
            item = NewsItem()
            item['date_post'] = self.get_date(response)
            item['date_post_local_time'] = self.get_date_post_local_time(response)
            item['author'] = self.get_author(response)
            item['title'] = self.get_title(response)
            item['link'] = response.url
            item['tags'] = self.get_tags(response)
            item['source'] = self.name
            if item['tags'] and item['date_post']:
                yield item

    def get_date_post_local_time(self, response):
        new_time = response.css('.article-image span::text').get().replace(',','').replace('|','').split(' ')
        new_time = [item for item in new_time if remove_day(item) and item.upper() != 'WIB' and item != '']
        return '{}-{}-{} {}'.format(
            new_time[0], 
            to_number_of_month(new_time[1].lower()),
            new_time[2],
            new_time[3])

    def get_author(self, response):
        return response.css('.article-image h3 a::text').get().strip()
    
    def get_title(self, response):
        return response.css('.article-image h1::text').get().strip()

    def get_date(self, response):
        date = self.get_date_post_local_time(response)
        if date:
            return new_date_parse(date)
        return None

    def get_tags(self, response):
        tags = response.css('.article-tags a::text').getall()
        if tags:
            tags = [tag.replace('#','').strip() if '#' in tag else tag.strip() for tag in tags]
            return tags
        return None