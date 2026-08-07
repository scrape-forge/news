# -*- coding: utf-8 -*-
import scrapy
from news.lib import remove_tabs, new_date_parse, remove_day, to_number_of_month
from news.items import NewsItem


class MerdekaSpider(scrapy.Spider):
    name = 'merdeka'
    allowed_domains = ['merdeka.com']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
    }
    start_urls = [
        'https://www.merdeka.com/peristiwa',
        'https://www.merdeka.com/politik',
        'https://www.merdeka.com/uang',
        'https://www.merdeka.com/trending'
    ]

    def parse(self, response):
        for href in response.css('.box.box-news li .item-detail span.item-title a::attr(href)').getall():
            detail_page = '{}{}'.format('https://www.merdeka.com', href)
            yield scrapy.Request(detail_page, callback=self.parse_detail)

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
        return self.clean_content(response)

    def clean_content(self, response):
        content_lst = response.css('.mdk-body-paragraph p ::text').getall()
        if content_lst:
            content = '\n\n'.join(content_lst)
            return remove_tabs(content)
        return None

    def get_title(self, response):
        return response.css('h1.article-title::text').get()

    def get_author(self, response):
        return response.css('.dt--postcredit-editor-desc span a::text').get().title()

    def get_date_post_local_time(self, response):
        new_time = response.css('.article time span::text').getall()
        new_time = new_time[0].split() + [new_time[1]]
        new_time = [item for item in new_time if remove_day(item.replace(',','')) and item.upper() != 'WIB']
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
        return response.css('.box-list.box-list--related .box-list-item a::attr(title)').getall()