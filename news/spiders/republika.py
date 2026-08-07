# -*- coding: utf-8 -*-
# v2.0 — Refactored to RSS (legal, stable)
# Feeds: republika.co.id/rss/{category} — multiple categories combined
#
# Note: Republika provides per-category RSS feeds. We subscribe to the
# most relevant news categories. Author is available via dc:creator.
from news.spiders.base_rss import RSSBaseSpider


class RepublikaSpider(RSSBaseSpider):
    name   = 'republika'
    source = 'republika'
    rss_url = [
        {'url': 'https://www.republika.co.id/rss/nasional/', 'category': 'Nasional'},
        {'url': 'https://www.republika.co.id/rss/ekonomi/', 'category': 'Ekonomi'},
        {'url': 'https://www.republika.co.id/rss/internasional/', 'category': 'Internasional'},
        {'url': 'https://www.republika.co.id/rss/olahraga/', 'category': 'Olahraga'},
    ]