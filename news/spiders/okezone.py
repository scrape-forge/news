# -*- coding: utf-8 -*-
# v2.0 — Refactored to RSS (legal, stable)
# Feed: http://sindikasi.okezone.com/index.php/okezone/RSS2.0
#
# Note: Okezone provides a syndication RSS endpoint (sindikasi.okezone.com).
# This is their official feed distribution service designed for aggregators.
from news.spiders.base_rss import RSSBaseSpider


class OkezoneSpider(RSSBaseSpider):
    name    = 'okezone'
    source  = 'okezone'
    rss_url = 'http://sindikasi.okezone.com/index.php/okezone/RSS2.0'