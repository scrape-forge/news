# -*- coding: utf-8 -*-
import scrapy
from news.items import NewsItem
from news.lib import remove_tabs, new_date_parse, to_number_of_month


class OkezoneSpider(scrapy.Spider):
    name = 'okezone'
    allowed_domains = ['okezone.com']
    index_kanals_id = [1, 2, 11, 12, 13, 14, 16, 613,
                       25, 298, 481, 15, 337, 338, 619, 623, 620]
    base_url = 'https://index.okezone.com/home/channel/'

    def start_requests(self):
        for id in self.index_kanals_id:
            url = self.base_url + str(id)
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for href in response.css('ul.list-berita li h4 a::attr(href)'):
            yield scrapy.Request(url=href.get(), callback=self.parse_detail)

        has_next_page = None
        has_next_page = response.css('.pagination-indexs a::text').getall()
        if has_next_page:
            if 'next' in str(has_next_page[-1]).lower():
                next_pages = response.css('.pagination-indexs a::attr(href)').getall()
                if next_pages:
                    next_page = next_pages[-1]
                    yield scrapy.Request(next_page, callback=self.parse)

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
        content_lst = response.css('#contentx p::text').getall()
        if content_lst:
            return remove_tabs('\n\n'.join(content_lst))
        return None

    def get_title(self, response):
        return response.css('.title-article h1::text').get()

    def get_author(self, response):
        author = response.css('.journalist > a:last-of-type::text').get()
        if author:
            return author.replace('\n', '').strip()

    def get_date_post_local_time(self, response):
        time = response.css('.journalist > span ::text').get()
        if time:
            new_time = time.split(' ')[1:-1]
            new_time = [x.replace('|','') for x in new_time ]
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

    def get_tags(self, response):
        return response.css('#tag .box-tag a::text').getall()