# -*- coding: utf-8 -*-
# v2.0 — Refactored to RSS (legal, stable)
# Feed: https://www.tribunnews.com/rss
from news.spiders.base_rss import RSSBaseSpider


class TribunSpider(RSSBaseSpider):
    name    = 'tribun'
    source  = 'tribun'
    rss_url = 'https://www.tribunnews.com/rss'

    def get_category(self, entry, response) -> str | None:
        """
        Tribun's RSS XML lacks <category> tags.
        Extract it from the URL instead: https://www.tribunnews.com/{category}/...
        """
        link = self.get_link(entry)
        if link:
            parts = link.split('/')
            # ['https:', '', 'www.tribunnews.com', 'nasional', '7865402', '...']
            if len(parts) > 3 and 'tribunnews.com' in parts[2]:
                return parts[3].title()
        
        return super().get_category(entry, response)

    def get_tags(self, entry) -> list:
        """
        Tribun's RSS lacks <category> tags.
        We populate the tags list with the extracted URL category so it isn't empty.
        """
        link = self.get_link(entry)
        if link:
            parts = link.split('/')
            if len(parts) > 3 and 'tribunnews.com' in parts[2]:
                return [parts[3].title()]
        return super().get_tags(entry)