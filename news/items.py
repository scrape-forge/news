# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
#
# v2.0 changes:
#   - Added: summary (short excerpt, available from RSS feeds)
#   - Added: image_url (thumbnail image URL, available from RSS feeds)
#   - Removed: content (was defined but never populated — misleading)

import scrapy


class NewsItem(scrapy.Item):
    # --- Core fields (all sources) ---
    title                = scrapy.Field()  # Article headline
    author               = scrapy.Field()  # Author name (may be None for RSS sources)
    date_post            = scrapy.Field()  # Publication datetime in UTC
    date_post_local_time = scrapy.Field()  # Raw local datetime string (WIB)
    link                 = scrapy.Field()  # Canonical article URL
    tags                 = scrapy.Field()  # List of tag/category strings
    source               = scrapy.Field()  # Spider name (e.g. 'detik', 'antara')

    # --- Enriched fields (RSS sources only) ---
    summary              = scrapy.Field()  # Short article excerpt/description
    image_url            = scrapy.Field()  # Thumbnail image URL
