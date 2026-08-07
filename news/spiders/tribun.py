# -*- coding: utf-8 -*-
# v2.0 — Refactored to RSS (legal, stable)
# Feed: https://www.tribunnews.com/rss
from news.spiders.base_rss import RSSBaseSpider


class TribunSpider(RSSBaseSpider):
    name    = 'tribun'
    source  = 'tribun'
    rss_url = 'https://www.tribunnews.com/rss'