# -*- coding: utf-8 -*-
"""Liputan6 spider backed by the publisher's public RSS feeds."""

from news.spiders.base_rss import RSSBaseSpider


class Liputan6Spider(RSSBaseSpider):
    name = 'liputan6'
    source = 'liputan6'
    rss_url = [
        {
            'url': 'https://feed.liputan6.com/rss/news',
            'category': 'News',
        },
        {
            'url': 'https://feed.liputan6.com/rss/bisnis',
            'category': 'Bisnis',
        },
        {
            'url': 'https://feed.liputan6.com/rss/bola',
            'category': 'Bola',
        },
        {
            'url': 'https://feed.liputan6.com/rss/tekno',
            'category': 'Teknologi',
        },
        {
            'url': 'https://feed.liputan6.com/rss/showbiz',
            'category': 'Showbiz',
        },
        {
            'url': 'https://feed.liputan6.com/rss/lifestyle',
            'category': 'Lifestyle',
        },
        {
            'url': 'https://feed.liputan6.com/rss/health',
            'category': 'Kesehatan',
        },
        {
            'url': 'https://feed.liputan6.com/rss/otomotif',
            'category': 'Otomotif',
        },
    ]
