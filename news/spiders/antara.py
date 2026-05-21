# -*- coding: utf-8 -*-
import scrapy
import re
from news.lib import remove_tabs, new_date_parse, to_number_of_month, remove_day
from news.items import NewsItem
from urllib.parse import urlparse


class AntaraSpider(scrapy.Spider):
    name = 'antara'
    allowed_domains = ['www.antaranews.com']
    allowed_unit = ['menit','jam']
    start_urls = ['http://www.antaranews.com/terkini']
    category = 'berita'

    def parse(self, response):
        for content in response.css('.card__post__content'):
            ymd_content = content.css('.card__post__author-info.mb-2  span::text').get()
            ymd_list = ymd_content.split(' ')
            if len(ymd_list) >= 3 :
                unit = ymd_list[1]
                if unit not in self.allowed_unit:
                    continue
                else:
                    for href in response.css('.card__post__title a::attr(href)').getall():
                        parsed_url = urlparse(href)
                        path_parts = parsed_url.path.strip('/').split('/')
                        if path_parts[0].lower() != self.category:
                            continue
                        else:
                            yield scrapy.Request(url=href, callback=self.parse_detail)

        last_page = response.css('.pagination a::text')[-1].get()
        pages = ['{}/{}'.format('http://www.antaranews.com/terkini', x) for x in range(2, int(last_page) + 1)]
        
        for page in pages:
            yield scrapy.Request(url=page, callback=self.parse)

    def parse_detail(self, response):
        if re.search('.*www\.antaranews\.com\/berita*', response.url):
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

    def get_author(self, response):
        author = response.css('.container .text-muted::text').getall()[0]
        if author:
            return self.clean_author(author.lower())
        return None

    def get_title(self, response):
        return response.css('.container h1::text').get().strip().title()

    def get_content(self, response):
        content_lst = response.css('.post-content.clearfix::text').getall()
        if content_lst:
            return remove_tabs(''.join(content_lst))
        return None

    def get_date(self, response):
        date = self.get_date_post_local_time(response)
        if date:
            return new_date_parse(date)
        return None

    def get_date_post_local_time(self, response):
        new_time = response.css('.container .wrap__article-detail-info span::text').getall()[-2].replace(',','').strip().split(' ')
        new_time = [item for item in new_time if remove_day(item) and item.upper() != 'WIB']
        return '{}-{}-{} {}'.format(
            new_time[0], 
            to_number_of_month(new_time[1].lower()),
            new_time[2],
            new_time[3])


    def clean_author(self, author):
        for label in ['editor:', 'pewarta:', 'penerjemah:']:
            author = author.replace(label, '')
        return author.strip().title()

    def get_tags(self, response):
        return response.css('.blog-tags li a::text').getall()