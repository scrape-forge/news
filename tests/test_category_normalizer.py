from unittest import TestCase
from news.lib import normalize_category


class CategoryNormalizerTests(TestCase):
    def test_normalizes_economic_categories(self):
        self.assertEqual(normalize_category("Ekonomi Bisnis"), "Ekonomi & Bisnis")
        self.assertEqual(normalize_category("finance"), "Ekonomi & Bisnis")
        self.assertEqual(normalize_category("Market Update"), "Ekonomi & Bisnis")

    def test_normalizes_tech_categories(self):
        self.assertEqual(normalize_category("tekno"), "Teknologi & Sains")
        self.assertEqual(normalize_category("Techno"), "Teknologi & Sains")

    def test_normalizes_sports_categories(self):
        self.assertEqual(normalize_category("MotoGP"), "Olahraga")
        self.assertEqual(normalize_category("Liga Italia"), "Olahraga")

    def test_normalizes_generic_categories(self):
        self.assertEqual(normalize_category("Terkini"), "General")
        self.assertEqual(normalize_category("Berita"), "General")
        self.assertEqual(normalize_category(None), "General")
