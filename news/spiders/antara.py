# -*- coding: utf-8 -*-
# v2.0 — Refactored to RSS (legal, stable)
# Feed: https://www.antaranews.com/rss/terkini.xml
from news.spiders.base_rss import RSSBaseSpider


class AntaraSpider(RSSBaseSpider):
    name    = 'antara'
    source  = 'antara'
    rss_url = 'https://www.antaranews.com/rss/terkini.xml'