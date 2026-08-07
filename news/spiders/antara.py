# -*- coding: utf-8 -*-
# v2.0 — Refactored to RSS (legal, stable)
# Feed: https://www.antaranews.com/rss/terkini.xml
from news.spiders.base_rss import RSSBaseSpider


class AntaraSpider(RSSBaseSpider):
    name    = 'antara'
    source  = 'antara'
    rss_url = [
        {'url': 'https://www.antaranews.com/rss/terkini.xml', 'category': 'Terkini'},
        {'url': 'https://www.antaranews.com/rss/top-news.xml', 'category': 'Top News'},
        {'url': 'https://www.antaranews.com/rss/politik.xml', 'category': 'Politik'},
        {'url': 'https://www.antaranews.com/rss/hukum.xml', 'category': 'Hukum'},
        {'url': 'https://www.antaranews.com/rss/ekonomi.xml', 'category': 'Ekonomi'},
        {'url': 'https://www.antaranews.com/rss/metro.xml', 'category': 'Metro'},
        {'url': 'https://www.antaranews.com/rss/sepakbola.xml', 'category': 'Sepakbola'},
        {'url': 'https://www.antaranews.com/rss/olahraga.xml', 'category': 'Olahraga'},
        {'url': 'https://www.antaranews.com/rss/humaniora.xml', 'category': 'Humaniora'},
        {'url': 'https://www.antaranews.com/rss/lifestyle.xml', 'category': 'Lifestyle'},
        {'url': 'https://www.antaranews.com/rss/hiburan.xml', 'category': 'Hiburan'},
        {'url': 'https://www.antaranews.com/rss/dunia.xml', 'category': 'Dunia'},
        {'url': 'https://www.antaranews.com/rss/tekno.xml', 'category': 'Tekno'},
        {'url': 'https://www.antaranews.com/rss/otomotif.xml', 'category': 'Otomotif'},
    ]