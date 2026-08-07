# -*- coding: utf-8 -*-
# v2.0 — Refactored to RSS (legal, stable)
# Feed: https://sindonews.com/feed
from news.spiders.base_rss import RSSBaseSpider


class SindoSpider(RSSBaseSpider):
    name    = 'sindo'
    source  = 'sindo'
    rss_url = 'https://sindonews.com/feed'