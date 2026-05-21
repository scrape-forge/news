# -*- coding: utf-8 -*-
import scrapy
import re
from news.items import NewsItem
from news.lib import remove_tabs, date_parse
from datetime import datetime
from urllib.parse import urlparse


class RepublikaSpider(scrapy.Spider):
    name = 'republika'
    allowed_domains = ['republika.co.id']
    date = datetime.now().strftime('%Y/%m/%d')
    start_urls = ['https://www.republika.co.id/index/{}'.format(date)]

    def parse(self, response):
        links = response.css('.txt_subkanal h2')
        if len(links) != 0:
            for href in links:
                url_page = href.css('a::attr(href)').get()
                yield scrapy.Request(url_page, callback=self.parse_detail)

            next_page = response.css('nav a::attr(href)').getall()
            if next_page:
                yield scrapy.Request(next_page[-1], callback=self.parse)

    def parse_detail(self, response):
        link_url = urlparse(response.url)
        if re.search('^republika', link_url.hostname):
            item = NewsItem()
            item['date_post'] = self.get_date(response)
            item['date_post_local_time'] = self.get_date_post_local_time(
                response)
            item['author'] = self.get_author(response)
            item['title'] = self.get_title(response)
            item['link'] = response.url
            item['tags'] = self.get_tags(response)
            item['source'] = self.name
            return item

    def get_content(self, response):
        return self.clean_content(response)

    def get_author(self, response):
        author = response.css('.by > span > p::text').get()
        if author:
            return self.clean_author(author)
        return None

    def clean_author(self, author_str):
        author_lst = str(author_str).strip().replace(
            '\n', '').strip().split(':')
        author_lst = [x.replace('Red', '').replace(
            'Rep', '').replace('/', '').strip() for x in author_lst]
        author_lst = [x for x in author_lst if len(x) != 0]
        author = ' - '.join(author_lst) if len(
            author_lst) > 1 else ''.join(author_lst)
        return author.title()

    def clean_content(self, response):
        content_lst = response.css('.artikel  p ::text').getall()
        if content_lst:
            content = remove_tabs('\n'.join(content_lst))
        else:
            content_lst = response.css(
                '[itemprop="articleBody"] p::text').getall()
            content = remove_tabs('\n'.join(content_lst))
        return content

    def get_date_post_local_time(self, response):
        date_string = response.css('.date_detail p::text').get()
        if date_string:
            return re.sub('[ ]+', ' ', date_string)
        return None

    def get_title(self, response):
        return response.css('.wrap_detail_set h1::text').get()

    def get_date(self, response):
        date = self.get_date_post_local_time(response)
        if date:
            return date_parse(date)
        return None

    def get_tags(self, response):
        return response.css('.wrap_blok_tag a::text').getall()