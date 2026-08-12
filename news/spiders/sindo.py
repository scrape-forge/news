# -*- coding: utf-8 -*-
# v2.0 — Refactored to RSS (legal, stable)
# Feed: https://sindikasi.sindonews.com/
from news.spiders.base_rss import RSSBaseSpider


class SindoSpider(RSSBaseSpider):
    name    = 'sindo'
    source  = 'sindo'
    rss_url = 'https://sindikasi.sindonews.com/'
