from datetime import datetime, timedelta, timezone
from unittest import TestCase

from news.spiders.time_window import LOCAL_TZ, RecentWindowMixin


class _Settings:
    def getint(self, name, default):
        return default


class _Window(RecentWindowMixin):
    settings = _Settings()


class RecentWindowMixinTests(TestCase):
    def setUp(self):
        self.window = _Window()
        self.end = datetime(2026, 8, 12, 4, tzinfo=timezone.utc)
        self.window._window_end_utc = self.end
        self.window._window_start_utc = self.end - timedelta(hours=24)

    def test_accepts_both_window_boundaries(self):
        self.assertTrue(self.window.is_in_window(self.end))
        self.assertTrue(
            self.window.is_in_window(self.end - timedelta(hours=24))
        )

    def test_rejects_article_older_than_window(self):
        self.assertFalse(
            self.window.is_in_window(
                self.end - timedelta(hours=24, seconds=1)
            )
        )

    def test_naive_datetime_is_interpreted_as_jakarta_time(self):
        local_end = self.end.astimezone(LOCAL_TZ).replace(tzinfo=None)
        self.assertTrue(self.window.is_in_window(local_end))

    def test_rejects_missing_date(self):
        self.assertFalse(self.window.is_in_window(None))
