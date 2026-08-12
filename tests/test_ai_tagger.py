from unittest import TestCase
from unittest.mock import patch, MagicMock

from news.ai_tagger import generate_ai_tags
from news.lib import normalize_tags


class AITaggerTests(TestCase):
    @patch.dict('os.environ', {}, clear=True)
    def test_returns_empty_when_no_api_key(self):
        tags = generate_ai_tags("Jokowi Tinjau IKN", "Presiden meninjau pembangunan")
        self.assertEqual(tags, [])

    @patch.dict('os.environ', {'GROQ_API_KEY': 'mock_key'})
    @patch('requests.post')
    def test_parses_valid_ai_tags(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {'message': {'content': '["IKN", "Politik", "Pembangunan"]'}}
            ]
        }
        mock_post.return_value = mock_response

        tags = generate_ai_tags("Jokowi Tinjau IKN", "Presiden meninjau pembangunan")
        self.assertEqual(tags, ["Ikn", "Politik", "Pembangunan"])

    def test_normalize_tags_extracts_local_patterns(self):
        tags = normalize_tags(raw_tags=["berita"], title="BI Tahan Suku Bunga 6.25%", summary="Bank Indonesia menahan suku bunga")
        self.assertIn("Suku Bunga BI", tags)

