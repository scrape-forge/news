# -*- coding: utf-8 -*-
import scrapy
import re
from news.lib import remove_tabs, date_parse
from news.items import NewsItem
from datetime import datetime


class TempoSpider(scrapy.Spider):
    name = 'tempo'
    allowed_domains = ['tempo.co']
    start_urls = ['https://tempo.co/indeks']

    def parse(self, response):
        for url in response.css('.text-card a::attr(href)').getall():
            yield scrapy.Request(url=url, callback=self.parse_detail)

    def parse_detail(self, response):
        if re.search('.*nasional\.tempo.*|.*bisnis\.tempo.*|.*metro\.tempo.*|.*dunia\.tempo.*', response.url):
            item = NewsItem()
            item['date_post'] = self.get_date(response)
            item['date_post_local_time'] = self.get_date_post_local_time(
                response)
            item['author'] = self.get_author(response)
            item['title'] = self.get_title(response)
            item['link'] = response.url
            item['tags'] = self.get_tags(response)
            item['source'] = self.name

            if item['tags'] and item['date_post']:
                yield item


    def get_date_post_local_time(self, response):
        date_string = response.css('span#date::text').get()
        if not date_string:
            date_string = response.css('.detail-title .date::text').get()
        return date_string

    def get_title(self, response):
        title = response.css('#article h1 ::text').get()
        if title:
            title = title.replace('\t', '').replace('\r', '').strip()
        else:
            title = response.css('.detail-title h1::text').get()
            if title:
                title = title.replace('\t', '').replace('\r', '').strip()
        return title

    def get_author(self, response):
        author = None
        author_lst = response.css('#article #author ::text').getall()
        author_lst = [re.sub('[\r\t\n]', '', x).lower()
                      for x in author_lst]
        author_lst = [x.replace('editor:', '').replace(
            'reporter:', '').replace(' ', '') for x in author_lst]
        author_lst = [x for x in author_lst if len(x) != 0]
        if author_lst:
            author = ' - '.join(author_lst).title()
        else:
            author = response.css(
                '.detail-title > div > div:nth-child(2) > div > h4.title.bold > a > span::text').get()
            if author:
                author = author.title()
        return author

    def get_date(self, response):
        date = self.get_date_post_local_time(response)
        if date:
            return date_parse(date)
        return None

    def get_tags(self, response):
        tags = response.css('.box-tag-detail a::text').getall()
        if tags:
            return tags
        return None