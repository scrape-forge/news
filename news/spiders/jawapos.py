# -*- coding: utf-8 -*-
# v2.0 — Refactored to RSS (legal, stable)
# Feeds: jawapos.com/{category}/rss — multiple categories
#
# Note: Jawapos provides per-category RSS feeds. This replaces the
# previous GraphQL API approach, which required private API access.
# Category RSS feeds are public and explicitly intended for consumption.
from news.spiders.base_rss import RSSBaseSpider


class JawaposSpider(RSSBaseSpider):
    name   = 'jawapos'
    source = 'jawapos'
    rss_url = [
        'https://www.jawapos.com/nasional/rss',
        'https://www.jawapos.com/ekonomi/rss',
        'https://www.jawapos.com/politik/rss',
        'https://www.jawapos.com/internasional/rss',
        'https://www.jawapos.com/pendidikan/rss',
        'https://www.jawapos.com/jabodetabek/rss',
    ]
