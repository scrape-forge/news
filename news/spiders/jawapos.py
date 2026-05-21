# -*- coding: utf-8 -*-
import scrapy
import json
from datetime import datetime, timedelta
from news.lib import new_date_parse
from news.items import NewsItem


class JawaposSpider(scrapy.Spider):
    name = 'jawapos'
    allowed_domains = ['jawapos.com']
    base_url = 'https://www.jawapos.com'
    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'Origin': 'https://www.jawapos.com',
            'Referer': 'https://www.jawapos.com/',
        }
    }
    categories = [
        '019c7e04-4bb9-7292-be09-859aac628495', # berika daerah
        '019c7e04-4bb8-7120-ab8e-7d1145fb7f70', # nasional
        '019c7e04-4bc5-7278-af0a-7221f5199685', # politik
        '019c7e04-4bcd-7325-80ae-414539b21b31', # ekonomi
        '019c7e04-4bce-70f8-9ca5-e7d69b61bee7', # bisnis
        '019c7e04-4bd2-72ec-90de-04045cf24c2c', # finance
        '019c7e04-4bd5-7142-a662-5b22f90af89f', # international
        '019c7e04-4bbb-71d1-89b5-fffc45efc6a6', # pendidikan
        '019c7e04-4bd8-7146-9a7e-14a755c52685', # jabodetabek
    ]

    gql_url = 'https://api.jawapos.com/api-jp-graphql'
    gql_query = """
    query SearchArticles($filter: SearchArticleFilter, $first: Int, $page: Int) {
        searchArticle(filter: $filter, first: $first, page: $page) {
            paginatorInfo {
                hasMorePages
            }
            data {
                ...ListArticleFields
                authors {
                    ...CoreReporterFields
                }
                category {
                    ...CoreCategoryFields
                }
                tags {
                    ...CoreTagsFields
                }
            }
        }
    }

    fragment ListArticleFields on Article {
        id
        article_id
        title
        slug
        description
        cover
        published_at
    }

    fragment CoreCategoryFields on Category {
        id
        name
        slug
    }

    fragment CoreReporterFields on Reporter {
        id
        name
        slug
    }

    fragment CoreTagsFields on Tag {
        id
        name
        slug
    }
    """

    def start_requests(self):
            now = datetime.now()
            today = now.strftime("%Y-%m-%d")
            # yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            
            for category in self.categories:
                yield self.make_request(category, today, today, page=1)

    def make_request(self, category, today, yesterday, page):
        """Build and return a GraphQL POST request for a given category and page."""
        variables = {
            "filter": {
                "publisherId": "1",
                "categoryId": category,
                "dateStart": f"{yesterday} 00:00:00",
                "dateEnd": f"{today} 23:59:59",
            },
            "first": 100,
            "page": page
        }
        payload = {
            "query": self.gql_query,
            "variables": variables
        }
        return scrapy.Request(
            url=self.gql_url,
            method='POST',
            body=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            callback=self.parse,
            cb_kwargs={
                'category': category,
                'today': today,
                'yesterday': yesterday,
                'page': page,
            }
        )
        
    def parse(self, response, category, today, yesterday, page):
        data = json.loads(response.text)
        search_result = data.get('data', {}).get('searchArticle', {})
        articles = search_result.get('data', [])
        has_more_pages = search_result.get('paginatorInfo', {}).get('hasMorePages', False)

        for article in articles:
            yield self.parse_detail(article)

        # If there are more pages, request the next one
        if has_more_pages:
            self.logger.info(f"Category {category} has more pages, fetching page {page + 1}")
            yield self.make_request(category, today, yesterday, page=page + 1)

    def parse_detail(self, article):
        item = NewsItem()
        item['date_post'] = self.get_date(article)
        item['date_post_local_time'] = self.get_date_post_local_time(article)
        item['author'] = self.get_author(article)
        item['title'] = self.get_title(article)
        item['link'] = self.get_url(article)
        item['source'] = self.name
        item['tags'] = self.get_tags(article)
        return item

    def get_author(self, item):
        return item.get('authors',[])[0].get('name')

    def get_title(self, item):
        return item.get('title')

    def get_date_post_local_time(self, item):
        return item.get('published_at')

    def get_date(self, item):
        date_id = self.get_date_post_local_time(item)
        if date_id:
            return new_date_parse(date_id)
        return None

    def get_tags(self, item):
        return [tag.get('name') for tag in item.get('tags')]
    
    def get_url(self, item):
        return '{}/{}/{}/{}'.format(
            self.base_url,
            item.get('category', {}).get('slug'),
            item.get('article_id'),
            item.get('slug')
        )
