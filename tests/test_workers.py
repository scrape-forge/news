from unittest import TestCase
from unittest.mock import MagicMock, patch

from news.workers import cli, enrich_articles
from news.workers.common.groq import GroqResult


VALID_ENRICHMENT = {
    "tags": ["Bank Indonesia", "Inflasi"],
    "sentiment": 0.45,
    "sentiment_label": "Positive",
    "bullets": ["BI mempertahankan suku bunga.", "Rupiah menjadi fokus kebijakan."],
    "entities": {
        "companies": ["Bank Indonesia"],
        "people": ["Perry Warjiyo"],
        "locations": ["Jakarta"],
    },
    "sector": "Banking & Finance",
}


class WorkerCliTests(TestCase):
    @patch("news.workers.cli.enrich_articles.run", return_value=0)
    def test_dispatches_enrichment_worker_with_options(self, mock_run):
        exit_code = cli.main(
            ["enrich", "--batch-size", "7", "--max-requests", "3"]
        )

        self.assertEqual(exit_code, 0)
        mock_run.assert_called_once_with(batch_size=7, max_requests=3)


class EnrichArticlesWorkerTests(TestCase):
    def test_fetch_claims_unenriched_rows_without_waiting(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = [(1, "Title", "Summary", ["Existing"])]

        articles = enrich_articles.fetch_unenriched_articles(
            cursor,
            limit=10,
            attempted_ids={8, 9},
        )

        self.assertEqual(articles, [(1, "Title", "Summary", ["Existing"])])
        query = cursor.execute.call_args.args[0]
        self.assertIn("ai_enriched_at IS NULL", query)
        self.assertIn("FOR UPDATE SKIP LOCKED", query)
        attempted, limit = cursor.execute.call_args.args[1]
        self.assertEqual(set(attempted), {8, 9})
        self.assertEqual(limit, 10)

    @patch("news.workers.enrich_articles.request_json_completion")
    def test_batch_call_returns_enrichment_and_detects_low_quota(self, mock_request):
        mock_request.return_value = GroqResult(
            content={"42": VALID_ENRICHMENT},
            status_code=200,
            remaining_tokens=1000,
            remaining_requests=8,
        )

        enrichment_map, quota_exhausted = enrich_articles.call_groq_batch(
            [(42, "BI Tahan Bunga", "Berita terbaru", ["Ekonomi"])],
            "api-key",
        )

        self.assertEqual(enrichment_map, {"42": VALID_ENRICHMENT})
        self.assertTrue(quota_exhausted)

    def test_normalizes_full_papagon_enrichment(self):
        normalized = enrich_articles.normalize_enrichment(
            VALID_ENRICHMENT,
            existing_tags=["Ekonomi", "Inflasi"],
        )

        self.assertEqual(
            normalized["tags"],
            ["Ekonomi", "Inflasi", "Bank Indonesia"],
        )
        self.assertEqual(normalized["sentiment_score"], 0.45)
        self.assertEqual(normalized["sentiment_label"], "Positive")
        self.assertEqual(normalized["sector"], "Banking & Finance")
        self.assertEqual(normalized["entities"]["people"], ["Perry Warjiyo"])

    def test_rejects_incomplete_enrichment(self):
        invalid = {**VALID_ENRICHMENT, "bullets": ["Only one bullet"]}

        self.assertIsNone(enrich_articles.normalize_enrichment(invalid))

    def test_updates_only_claimed_valid_articles(self):
        cursor = MagicMock()
        cursor.rowcount = 1
        connection = MagicMock()

        updated = enrich_articles.update_article_enrichments(
            cursor,
            connection,
            {
                "42": VALID_ENRICHMENT,
                "99": VALID_ENRICHMENT,
                "invalid": VALID_ENRICHMENT,
            },
            claimed_articles={42: ["Ekonomi"]},
        )

        self.assertEqual(updated, 1)
        self.assertEqual(cursor.execute.call_count, 1)
        query, params = cursor.execute.call_args.args
        self.assertIn("ai_enriched_at = NOW()", query)
        self.assertEqual(params[0], ["Ekonomi", "Bank Indonesia", "Inflasi"])
        self.assertEqual(params[1:4], (0.45, "Positive", VALID_ENRICHMENT["bullets"]))
        self.assertEqual(params[-2:], ("Banking & Finance", 42))
        connection.commit.assert_called_once_with()

    def test_settings_are_bounded(self):
        value = enrich_articles._bounded_setting(
            100,
            env_name="BATCH_SIZE",
            default=5,
            maximum=5,
        )

        self.assertEqual(value, 5)
