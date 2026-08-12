# -*- coding: utf-8 -*-
"""Helpers for extracting Schema.org NewsArticle metadata."""

import json

from dateutil.parser import isoparse


def _iter_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_dicts(child)


def _news_article_node(response):
    scripts = response.css(
        'script[type="application/ld+json"]::text'
    ).getall()
    for raw in scripts:
        try:
            payload = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            continue
        for node in _iter_dicts(payload):
            node_type = node.get('@type')
            types = node_type if isinstance(node_type, list) else [node_type]
            if 'NewsArticle' in types or 'Article' in types:
                return node
    return {}


def _author_name(value):
    if isinstance(value, list):
        names = [_author_name(author) for author in value]
        return ', '.join(name for name in names if name) or None
    if isinstance(value, dict):
        return value.get('name')
    return value if isinstance(value, str) else None


def _image_url(value):
    if isinstance(value, list):
        return _image_url(value[0]) if value else None
    if isinstance(value, dict):
        return value.get('url') or value.get('contentUrl')
    return value if isinstance(value, str) else None


def _keywords(value):
    if isinstance(value, list):
        return [
            str(keyword).strip()
            for keyword in value
            if str(keyword).strip()
        ]
    if isinstance(value, str):
        if value.lstrip().startswith('['):
            try:
                return _keywords(json.loads(value))
            except json.JSONDecodeError:
                pass
        return [
            keyword.strip()
            for keyword in value.split(',')
            if keyword.strip()
        ]
    return []


def _parse_date(value):
    try:
        return isoparse(value) if value else None
    except (TypeError, ValueError):
        return None


def iter_sitemap_locations(response):
    for node in response.xpath('//*[local-name()="sitemap"]'):
        yield {
            'url': node.xpath(
                './*[local-name()="loc"]/text()'
            ).get(),
            'modified_at': _parse_date(
                node.xpath('./*[local-name()="lastmod"]/text()').get()
            ),
        }


def iter_news_sitemap_entries(response):
    for node in response.xpath('//*[local-name()="url"]'):
        published = node.xpath(
            './/*[local-name()="publication_date"]/text()'
        ).get() or node.xpath('./*[local-name()="lastmod"]/text()').get()
        yield {
            'url': node.xpath('./*[local-name()="loc"]/text()').get(),
            'published_at': _parse_date(published),
            'title': node.xpath(
                './/*[local-name()="title"]/text()'
            ).get(),
            'tags': _keywords(
                node.xpath(
                    './/*[local-name()="keywords"]/text()'
                ).get()
            ),
            'image_url': node.xpath(
                './/*[local-name()="image"]/*[local-name()="loc"]/text()'
            ).get(),
        }


from news.lib import clean_headline, clean_summary, normalize_tags, normalize_category


def extract_article_data(response):
    node = _news_article_node(response)
    published = node.get('datePublished') or response.css(
        'meta[property="article:published_time"]::attr(content)'
    ).get()
    published_at = _parse_date(published)

    keywords = _keywords(node.get('keywords'))
    if not keywords:
        keywords = _keywords(
            response.css('meta[name="keywords"]::attr(content)').get()
        )

    raw_title = node.get('headline') or response.css(
        'meta[property="og:title"]::attr(content)'
    ).get() or ""

    raw_summary = node.get('description') or response.css(
        'meta[name="description"]::attr(content)'
    ).get() or ""

    title = clean_headline(raw_title)
    summary = clean_summary(raw_summary) if raw_summary else None
    tags = normalize_tags(raw_tags=keywords, title=title, summary=summary or "")
    raw_cat = node.get('articleSection')

    return {
        'title': title,
        'author': _author_name(node.get('author')) or response.css(
            'meta[name="author"]::attr(content)'
        ).get(),
        'published_at': published_at,
        'category': normalize_category(raw_cat),
        'tags': tags,

        'summary': summary,
        'image_url': _image_url(node.get('image')) or response.css(
            'meta[property="og:image"]::attr(content)'
        ).get(),
    }

