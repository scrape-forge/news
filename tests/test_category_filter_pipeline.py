from unittest import TestCase
from scrapy.exceptions import DropItem
from news.pipelines import CategoryFilterPipeline


class CategoryFilterPipelineTests(TestCase):
    def test_passes_allowed_categories(self):
        pipeline = CategoryFilterPipeline(allowed_categories=['Ekonomi & Bisnis', 'Politik & Hukum'])
        item = {'title': 'BI Rate', 'category': 'Ekonomi & Bisnis'}
        result = pipeline.process_item(item)
        self.assertEqual(result, item)

    def test_drops_unwanted_categories(self):
        pipeline = CategoryFilterPipeline(allowed_categories=['Ekonomi & Bisnis', 'Politik & Hukum'])
        item = {'title': 'Gossip Seleb', 'category': 'Hiburan & Seleb'}
        with self.assertRaises(DropItem):
            pipeline.process_item(item)

    def test_passes_all_when_allowed_categories_empty(self):
        pipeline = CategoryFilterPipeline(allowed_categories=[])
        item = {'title': 'Anything', 'category': 'Olahraga'}
        result = pipeline.process_item(item)
        self.assertEqual(result, item)
