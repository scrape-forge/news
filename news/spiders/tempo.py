# -*- coding: utf-8 -*-
# v2.0 — Refactored to RSS (legal, stable)
from news.spiders.base_rss import RSSBaseSpider


class TempoSpider(RSSBaseSpider):
    name    = 'tempo'
    source  = 'tempo'
    rss_url = [
        {'url': 'https://rss.tempo.co/nasional', 'category': 'Nasional'},
        {'url': 'https://rss.tempo.co/bisnis', 'category': 'Bisnis'},
        {'url': 'https://rss.tempo.co/metro', 'category': 'Metro'},
        {'url': 'https://rss.tempo.co/dunia', 'category': 'Dunia'},
        {'url': 'https://rss.tempo.co/bola', 'category': 'Bola'},
        {'url': 'https://rss.tempo.co/sport', 'category': 'Sport'},
        {'url': 'https://rss.tempo.co/cantik', 'category': 'Cantik'},
        {'url': 'https://rss.tempo.co/tekno', 'category': 'Tekno'},
        {'url': 'https://rss.tempo.co/otomotif', 'category': 'Otomotif'},
        {'url': 'https://rss.tempo.co/seleb', 'category': 'Seleb'},
        {'url': 'https://rss.tempo.co/gaya', 'category': 'Gaya'},
    ]

    def get_image(self, entry) -> str | None:
        """Tempo uses a custom <img> tag in their XML."""
        img_url = entry.findtext('img')
        if img_url:
            return img_url.strip()
        return super().get_image(entry)

    def get_category(self, entry, response) -> str | None:
        """
        Tempo's RSS lacks a category element, so derive only the category
        from the article subdomain. Do not expose it as a topical tag.
        """
        link = self.get_link(entry)
        if link:
            parts = link.split('/')
            # e.g., https://nasional.tempo.co/read/...
            if len(parts) > 2 and 'tempo.co' in parts[2]:
                subdomain = parts[2].split('.')[0]
                if subdomain != 'www':
                    return subdomain.title()
        return super().get_category(entry, response)
