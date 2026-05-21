# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
from news.items import NewsItem
from news.lib import date_parse
from json import loads


class TribunSpider(scrapy.Spider):
    name = 'tribun'
    allowed_domains = ['tribunnews.com']
    date = datetime.now().strftime('%Y-%m-%d')
    start_urls = [
        'https://www.tribunnews.com/indeks/news'
    ]

    def parse(self, response):
        last_page = response.css(
            ".paging a::attr(href)").getall()[-1].split('page=')
        pages = int(last_page[1])
        for page in range(2, pages+1):
            next_page = last_page[0] + "page=" + str(page)
            yield scrapy.Request(next_page, callback=self.parse)

        urls = response.css('h3 a::attr(href)').getall()
        for url in urls:
            yield scrapy.Request(url+"?page=all", callback=self.parse_detail)

    def parse_detail(self, response):
        item = NewsItem()
        item['date_post'] = self.get_date(response)
        item['date_post_local_time'] = self.get_date_post_local_time(response)
        item['author'] = self.get_author(response)
        item['title'] = self.get_title(response)
        item['link'] = response.url
        item['tags'] = self.get_tags(response)
        item['source'] = self.name
        yield item

    def get_content(self, response):
        content_lst = response.css(
            '.side-article.txt-article p::text').getall()
        if content_lst:
            content = '\n'.join(content_lst)
            return content
        return None

    def get_title(self, response):
        content = response.css('.content')
        return content.css('h1::text').get().strip()

    def get_author(self, response):
        return self.parse_author(response)

    def parse_author(self, response):
        author = (
            response.css('#penulis a::text').get() or
            response.css('#editor a::text').get()
        )            
        if author:
            return author.strip()
        return None

    def get_date_post_local_time(self, response):
        content = response.css('.content')
        return content.css('#article time ::text').get().strip()

    def get_date(self, response):
        date = self.get_date_post_local_time(response)
        if date:
            return date_parse(date)
        return None

    def get_tags(self, response):
        tags = response.css('.tagcloud3 a::text').getall()
        if tags:
            return [tag.replace('#','').strip() if '#' else tag.strip() in tag for tag in tags]
        return None