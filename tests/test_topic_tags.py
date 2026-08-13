from unittest import TestCase

from news.lib import normalize_tags


class TopicTagNormalizerTests(TestCase):
    def test_normalize_tags_extracts_local_patterns(self):
        tags = normalize_tags(
            raw_tags=["berita"],
            title="BI Tahan Suku Bunga 6.25%",
            summary="Bank Indonesia menahan suku bunga",
        )

        self.assertIn("Suku Bunga BI", tags)
