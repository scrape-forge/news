# -*- coding: utf-8 -*-
"""
Base class for RSS-based news spiders.

Subclasses only need to define:
    name     (str)        — Scrapy spider name
    rss_url  (str|list)   — RSS feed URL(s) to consume
    source   (str)        — Source label stored in each NewsItem (defaults to name)

Optionally override any get_* method to customize field extraction
for a specific source's RSS quirks.

Supported RSS namespaces (auto-handled):
    dc       → http://purl.org/dc/elements/1.1/          (author via dc:creator)
    content  → http://purl.org/rss/1.0/modules/content/  (content:encoded)
    media    → http://search.yahoo.com/mrss/              (media:content images)
    atom     → http://www.w3.org/2005/Atom

Example usage:

    from news.spiders.base_rss import RSSBaseSpider

    class AntaraSpider(RSSBaseSpider):
        name    = 'antara'
        rss_url = 'https://www.antaranews.com/rss/terkini.xml'
"""

import re
import pytz
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from lxml import etree

import scrapy
from news.items import NewsItem


# ---------------------------------------------------------------------------
# XML namespace map used across Indonesian news RSS feeds
# ---------------------------------------------------------------------------
NS = {
    'dc':      'http://purl.org/dc/elements/1.1/',
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'media':   'http://search.yahoo.com/mrss/',
    'atom':    'http://www.w3.org/2005/Atom',
    'slash':   'http://purl.org/rss/1.0/modules/slash/',
    'sy':      'http://purl.org/rss/1.0/modules/syndication/',
}

_HTML_TAG_RE  = re.compile(r'<[^>]+>')
_WHITESPACE_RE = re.compile(r'\s+')
_LOCAL_TZ     = pytz.timezone('Asia/Jakarta')
_SUMMARY_MAX  = 500  # max chars for summary field


def _strip_html(text: str) -> str:
    """Remove HTML tags and normalize whitespace from a string."""
    if not text:
        return ''
    text = _HTML_TAG_RE.sub(' ', text)
    text = _WHITESPACE_RE.sub(' ', text).strip()
    return text


# ---------------------------------------------------------------------------
# Base spider
# ---------------------------------------------------------------------------

class RSSBaseSpider(scrapy.Spider):
    """
    Reusable Scrapy base spider for consuming RSS/Atom feeds.

    Handles:
      - XML parsing with full namespace support
      - RFC 2822 date parsing → UTC datetime + WIB local string
      - Image extraction (media:content, enclosure, <img> in description)
      - HTML stripping for summary/excerpt
      - dc:creator author extraction
      - <category> tag extraction
    """

    # -- Required overrides in subclass --
    rss_url: str | list = None   # single URL or list of URLs

    # -- Optional override in subclass --
    source: str = None           # defaults to self.name if not set

    # RSS feeds are explicitly public endpoints — no delay needed
    custom_settings = {
        'DOWNLOAD_DELAY': 0,
        'AUTOTHROTTLE_ENABLED': False,
        'ROBOTSTXT_OBEY': False,
    }

    # ------------------------------------------------------------------ #
    # Scrapy lifecycle                                                     #
    # ------------------------------------------------------------------ #

    async def start(self):
        """Scrapy 2.13+ async start — yields one Request per RSS feed URL."""
        if not self.rss_url:
            raise ValueError(f'Spider "{self.name}" must define rss_url.')

        urls = [self.rss_url] if isinstance(self.rss_url, (str, dict)) else list(self.rss_url)
        for url_def in urls:
            if isinstance(url_def, dict):
                url = url_def['url']
                feed_category = url_def.get('category')
            else:
                url = url_def
                feed_category = None

            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'feed_category': feed_category},
                headers={
                    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                },
            )

    def parse(self, response):
        """Parse RSS XML and yield a NewsItem per <item>."""
        # recover=True allows lxml to handle malformed XML gracefully
        # (some feeds contain unescaped HTML entities or broken tags)
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        try:
            root = etree.fromstring(response.body, parser=parser)
        except Exception as exc:
            self.logger.error(f'RSS XML parse error from {response.url}: {exc}')
            return

        if root is None:
            self.logger.error(f'RSS XML root is None for {response.url} — skipping.')
            return

        entries = root.findall('.//item')
        self.logger.info(f'[{self.name}] {len(entries)} items found in {response.url}')

        for entry in entries:
            news_item = self._build_item(entry, response)
            if news_item:
                yield news_item

    # ------------------------------------------------------------------ #
    # Item builder                                                         #
    # ------------------------------------------------------------------ #

    def _build_item(self, entry, response) -> NewsItem | None:
        """
        Build a NewsItem from a single RSS <item> element.
        Parses date once and shares the result across both date fields.
        Returns None if the entry has no usable link.
        """
        link = self.get_link(entry)
        if not link:
            return None

        # Parse date once — shared between date_post and date_post_local_time
        dt_utc = self.get_date_utc(entry)

        item = NewsItem()
        item['title']                = self.get_title(entry)
        item['link']                 = link
        item['author']               = self.get_author(entry)
        item['date_post']            = dt_utc
        item['date_post_local_time'] = self._to_local_str(dt_utc)
        item['tags']                 = self.get_tags(entry)
        item['category']             = self.get_category(entry, response)
        item['source']               = self.source or self.name
        item['summary']              = self.get_summary(entry)
        item['image_url']            = self.get_image(entry)
        return item

    # ------------------------------------------------------------------ #
    # Field extractors (override in subclass to customise per source)     #
    # ------------------------------------------------------------------ #

    def get_title(self, entry) -> str | None:
        """Extract and clean the article headline from <title>."""
        title = entry.findtext('title')
        return title.strip() if title else None

    def get_link(self, entry) -> str | None:
        """
        Extract canonical article URL.
        Tries <link> first, falls back to <guid>.
        """
        link = entry.findtext('link') or entry.findtext('guid')
        return link.strip() if link else None

    def get_author(self, entry) -> str | None:
        """
        Extract author name.
        Tries dc:creator (Republika, standard WordPress) then <author>.
        """
        author = entry.findtext('dc:creator', namespaces=NS)
        if not author:
            author = entry.findtext('author')
        return author.strip().title() if author and author.strip() else None

    def get_date_utc(self, entry) -> datetime | None:
        """
        Parse <pubDate> (RFC 2822 format) → UTC-aware datetime.
        Example: "Fri, 07 Aug 2026 14:21:38 +0700"
        """
        pub_date = entry.findtext('pubDate')
        if not pub_date:
            return None
        try:
            dt = parsedate_to_datetime(pub_date.strip())
            return dt.astimezone(timezone.utc)
        except Exception as exc:
            self.logger.warning(f'Could not parse pubDate "{pub_date}": {exc}')
            return None

    def get_tags(self, entry) -> list:
        """Extract all <category> elements as a list of strings."""
        categories = entry.findall('category')
        return [
            c.text.strip()
            for c in categories
            if c.text and c.text.strip()
        ]

    def get_category(self, entry, response) -> str | None:
        """Extract primary category (defaults to first tag or explicit feed_category meta)."""
        tags = self.get_tags(entry)
        if tags:
            return tags[0]
        return response.meta.get('feed_category')

    def get_summary(self, entry) -> str | None:
        """
        Extract short article excerpt.
        Tries <description> (shorter, suitable for display) first,
        then falls back to <content:encoded> (longer, partial body).
        Strips all HTML tags. Capped at 500 characters.
        """
        # 1. <description>
        desc = entry.findtext('description')
        if desc:
            clean = _strip_html(desc)
            if clean:
                return clean[:_SUMMARY_MAX]

        # 2. <content:encoded>
        content = entry.findtext('content:encoded', namespaces=NS)
        if content:
            clean = _strip_html(content)
            if clean:
                return clean[:_SUMMARY_MAX]

        return None

    def get_image(self, entry) -> str | None:
        """
        Extract thumbnail image URL.
        Resolution order:
          1. <media:content url="..."> (Yahoo Media RSS extension)
          2. <enclosure url="..." type="image/...">
          3. First <img src="..."> found inside <description> HTML
        """
        # 1. media:content
        media_el = entry.find('media:content', namespaces=NS)
        if media_el is not None:
            url = media_el.get('url', '').strip()
            if url:
                return url

        # 2. <enclosure>
        enclosure = entry.find('enclosure')
        if enclosure is not None:
            enc_type = enclosure.get('type', '')
            enc_url  = enclosure.get('url', '').strip()
            if 'image' in enc_type and enc_url:
                return enc_url

        # 3. <img> inside description
        desc = entry.findtext('description') or ''
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc, re.IGNORECASE)
        if img_match:
            return img_match.group(1)

        return None

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _to_local_str(dt_utc: datetime | None) -> str | None:
        """
        Convert a UTC datetime to a WIB (Asia/Jakarta) local time string.
        Output format: 'DD-MM-YYYY HH:MM'
        """
        if not dt_utc:
            return None
        dt_local = dt_utc.astimezone(_LOCAL_TZ)
        return dt_local.strftime('%d-%m-%Y %H:%M')
