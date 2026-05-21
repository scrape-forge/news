# -*- coding: utf-8 -*-
import scrapy
from news.items import NewsItem
from news.lib import new_date_parse, remove_day, to_number_of_month


class SindoSpider(scrapy.Spider):
    name = 'sindo'
    allowed_domains = ['sindonews.com']
    start_urls = ['https://index.sindonews.com/indeks']

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        page = self.pages(response)
        if page:
            yield scrapy.Request(url=page, callback=self.parse)

        for href in response.css('.title-article.news-title a::attr(href)').getall():
            yield scrapy.Request(url=href+'?showpage=all', callback=self.parse_detail)

    def pages(self, response):
        pagination = response.xpath('//li[a[@class="active"]]/following-sibling::li[1]/a/@href').get()
        if pagination:
            return pagination
        return None
    
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

    def get_author(self, response):
        author = response.css('.article .reporter p a::text').get()
        if not author:
            author = response.css('.detail-nama-redaksi a::text').get()
        return author.title()

    def get_title(self, response):
        title = response.css('article h1.detail-title::text').get()
        if title:
            return title.strip()
        return None

    def get_date_post_local_time(self, response):
        date_string = response.css('.detail-date-artikel::text').get()
        if date_string:
            new_time = date_string.replace('- ', '').replace(',','').split(' ')
            new_time = [item for item in new_time if remove_day(item) and item.upper() != 'WIB']
            return '{}-{}-{} {}'.format(
                new_time[0], 
                to_number_of_month(new_time[1].lower()),
                new_time[2],
                new_time[3])
        return None

    def get_date(self, response):
        date = self.get_date_post_local_time(response)
        if date:
            return new_date_parse(date)
        return None

    def get_tags(self, response):
        tags = response.css('.article-tags a::text').getall()
        if tags:
            return tags
        return None