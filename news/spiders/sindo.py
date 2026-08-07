# -*- coding: utf-8 -*-
# v2.0 — Refactored to RSS (legal, stable)
# Feed: https://sindonews.com/feed
from news.spiders.base_rss import RSSBaseSpider


class SindoSpider(RSSBaseSpider):
    name    = 'sindo'
    source  = 'sindo'
    rss_url = [
        {'url': 'https://sindikasi.sindonews.com/rss/nasional', 'category': 'Nasional'},
        {'url': 'https://sindikasi.sindonews.com/rss/ekbis', 'category': 'Ekbis'},
        {'url': 'https://sindikasi.sindonews.com/rss/international', 'category': 'International'},
        {'url': 'https://sindikasi.sindonews.com/rss/daerah', 'category': 'Daerah'},
        {'url': 'https://sindikasi.sindonews.com/rss/sports', 'category': 'Sports'},
        {'url': 'https://sindikasi.sindonews.com/rss/soccer', 'category': 'Soccer'},
        {'url': 'https://sindikasi.sindonews.com/rss/lifestyle', 'category': 'Lifestyle'},
        {'url': 'https://sindikasi.sindonews.com/rss/edukasi', 'category': 'Edukasi'},
        {'url': 'https://sindikasi.sindonews.com/rss/otomotif', 'category': 'Otomotif'},
        {'url': 'https://sindikasi.sindonews.com/rss/tekno', 'category': 'Tekno'},
        {'url': 'https://sindikasi.sindonews.com/rss/kalam', 'category': 'Kalam'},
        {'url': 'https://sindikasi.sindonews.com/rss/video', 'category': 'Video'},
    ]