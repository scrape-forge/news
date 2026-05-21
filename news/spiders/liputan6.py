# -*- coding: utf-8 -*-
import scrapy
from news.items import NewsItem
from news.lib import remove_tabs, to_number_of_month, new_date_parse
from datetime import datetime

class Liputan6Spider(scrapy.Spider):
    name = 'liputan6'
    allowed_domains = ['www.liputan6.com']
    start_urls = [
        'http://www.liputan6.com/news',
        'http://www.liputan6.com/pilpres',
        'http://www.liputan6.com/pileg',
        'http://www.liputan6.com/bisnis'
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        contents = response.css('aside > header')
        for content in contents:
            datetimes = content.css('time::attr(datetime)').get()
            dt = datetime.fromisoformat(datetimes)
            is_today = dt.date() == datetime.now(dt.tzinfo).date()
            if is_today:
                yield scrapy.Request(url=content.css('h4 a::attr(href)').get(), callback=self.parse_detail)


    def parse_detail(self, response):
        item = NewsItem()
        item['date_post'] = self.get_date(response)
        item['date_post_local_time'] = self.get_date_post_local_time(response)
        item['author'] = self.get_author(response)
        item['title'] = self.get_title(response)
        item['link'] = response.url
        item['tags'] = self.get_tags(response)
        item['source'] = self.name
        return item

    def get_content(self, response):
        content_lst = response.css(
            '.article-content-body__item-content p::text').getall()
        if content_lst:
            content = remove_tabs('\n\n'.join(
                content_lst).replace('Baca Juga', ''))
            return content
        return None

    def get_title(self, response):
        return response.css('h1.read-page--header--title.entry-title::text').get()

    def get_author(self, response):
        author = response.css(
            '.read-page-box__author__name::text').get()
        if author:
            return str(author).title()

    def get_date_post_local_time(self, response):
        new_time = response.css('.read-page-box__author__updated::text').get().split(' ')
        new_time = [clean for item in new_time if (clean := item.replace('Diterbitkan','').replace(',','').strip()) and clean.upper() != 'WIB']
        return '{}-{}-{} {}'.format(
            new_time[0], 
            to_number_of_month(new_time[1].lower()),
            new_time[2],
            new_time[3])

    def get_date(self, response):
        date = self.get_date_post_local_time(response)
        if date:
            return new_date_parse(date)
        return None

    def get_tags(self, response):
        tags = response.css('.tags--snippet li a span::text').getall()
        if tags:
            return tags
        return None