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
    rss_url = [
        {'url': 'https://sindikasi.okezone.com/index.php/rss/0/RSS2.0',  'category': 'Breakingnews'},
        {'url': 'https://sindikasi.okezone.com/index.php/rss/1/RSS2.0',  'category': 'News'},
        {'url': 'https://sindikasi.okezone.com/index.php/rss/11/RSS2.0', 'category': 'Economy'},
        {'url': 'https://sindikasi.okezone.com/index.php/rss/12/RSS2.0', 'category': 'Lifestyle'},
        {'url': 'https://sindikasi.okezone.com/index.php/rss/13/RSS2.0', 'category': 'Celebrity'},
        {'url': 'https://sindikasi.okezone.com/index.php/rss/14/RSS2.0', 'category': 'Bola'},
        {'url': 'https://sindikasi.okezone.com/index.php/rss/2/RSS2.0',  'category': 'Sport'},
        {'url': 'https://sindikasi.okezone.com/index.php/rss/16/RSS2.0', 'category': 'Techno'},
    ]