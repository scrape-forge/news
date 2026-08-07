# -*- coding: utf-8 -*-
import scrapy
import tldextract as tld
from news.items import NewsItem
from news.lib import has_numbers, remove_day, new_date_parse, to_number_of_month
from datetime import datetime
from urllib.parse import urlencode


class DetikSpider(scrapy.Spider):
    name = 'detik'
    allowed_domains = ['detik.com']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
    }
    
    base_url = 'https://news.detik.com/indeks'
    params = {
    'date': datetime.now().strftime("%m/%d/%Y")
    } 
    start_urls = [
        f"{base_url}?{urlencode(params)}"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        pages = response.css('.pagination a::attr(href)').getall()
        
        # Fix parsing last page dari URL format ?page=N
        last_page = 1
        for page_url in reversed(pages):
            if 'page=' in page_url:
                try:
                    last_page = int(page_url.split("page=")[-1])
                    break
                except ValueError:
                    continue

        for page in range(2, last_page + 1):
            yield scrapy.Request(
                self.start_urls[0] + "&page=" + str(page),
                callback=self.parse
            )

        urls = response.css('.media__title a::attr(href)').getall()
        for href in urls:
            subdomain = tld.extract(href).subdomain
            if not has_numbers(subdomain):
                yield scrapy.Request(href, callback=self.parse_detail)



    def parse_detail(self, response):
        url_tags = self.parse_from_tags(response)
        for href in url_tags :
            subdomain = tld.extract(href).subdomain
            if not has_numbers(subdomain):
                yield scrapy.Request(href, callback=self.parse_detail)

        subdomain = tld.extract(response.url).subdomain
        if not has_numbers(subdomain):
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
        return self.content_parse(response)

    def content_parse(self, response):
        result = ''
        try:
            result = response.css('.detail__body-text  ::text').getall()
        except:
            pass
        return "".join(result)

    def get_date(self, response):
        date_str = self.get_date_post_local_time(response)
        if date_str:
            return new_date_parse(date_str)
        return None

    def get_date_post_local_time(self, response):
        new_time = response.css('.detail__date::text').get().replace(',','').split(' ')
        new_time = [item for item in new_time if remove_day(item) and item.upper() != 'WIB']
        return '{}-{}-{} {}'.format(
            new_time[0], 
            to_number_of_month(new_time[1].lower()),
            new_time[2],
            new_time[3])

    def get_author(self, response):
        return response.css('.detail__author::text').get().replace('-', '').strip().title()

    def get_title(self, response):
        headers = response.css('.detail')
        title = headers.css('h1::text').get()
        return title.strip() if title is not None else None

    def get_tags(self, response):
        return response.css('.nav [dtr-evt="tag"] ::text').getall()

    def parse_from_tags(self, response):
        return response.css('.list.media_rows.list-berita article a::attr(href)').getall()



