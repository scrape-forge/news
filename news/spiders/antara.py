# -*- coding: utf-8 -*-
# v2.0 — Refactored to RSS (legal, stable)
# Feed: https://www.antaranews.com/rss/terkini.xml
from news.spiders.base_rss import RSSBaseSpider


class AntaraSpider(RSSBaseSpider):
    name    = 'antara'
    source  = 'antara'
    rss_url = [
        'https://www.antaranews.com/rss/terkini.xml',
        'https://www.antaranews.com/rss/top-news.xml',
        'https://www.antaranews.com/rss/politik.xml',
        'https://www.antaranews.com/rss/hukum.xml',
        'https://www.antaranews.com/rss/ekonomi.xml',
        'https://www.antaranews.com/rss/metro.xml',
        'https://www.antaranews.com/rss/sepakbola.xml',
        'https://www.antaranews.com/rss/olahraga.xml',
        'https://www.antaranews.com/rss/humaniora.xml',
        'https://www.antaranews.com/rss/lifestyle.xml',
        'https://www.antaranews.com/rss/hiburan.xml',
        'https://www.antaranews.com/rss/dunia.xml',
        'https://www.antaranews.com/rss/tekno.xml',
        'https://www.antaranews.com/rss/otomotif.xml',
    ]