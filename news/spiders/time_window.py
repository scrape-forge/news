# -*- coding: utf-8 -*-
"""Shared rolling time-window helpers for news spiders."""

from datetime import datetime, timedelta, timezone

import pytz


LOCAL_TZ = pytz.timezone('Asia/Jakarta')


class RecentWindowMixin:
    """Restrict emitted articles to a configurable rolling time window."""

    default_lookback_hours = 24

    @property
    def lookback_hours(self):
        return self.settings.getint(
            'NEWS_LOOKBACK_HOURS',
            self.default_lookback_hours,
        )

    def window_bounds_utc(self):
        if not hasattr(self, '_window_end_utc'):
            self._window_end_utc = datetime.now(timezone.utc)
            self._window_start_utc = self._window_end_utc - timedelta(
                hours=self.lookback_hours,
            )
        return self._window_start_utc, self._window_end_utc

    def window_bounds_local(self):
        start_utc, end_utc = self.window_bounds_utc()
        return start_utc.astimezone(LOCAL_TZ), end_utc.astimezone(LOCAL_TZ)

    def is_in_window(self, published_at):
        if published_at is None:
            return False
        if published_at.tzinfo is None:
            published_at = LOCAL_TZ.localize(published_at).astimezone(
                timezone.utc
            )
        else:
            published_at = published_at.astimezone(timezone.utc)

        start_utc, end_utc = self.window_bounds_utc()
        return start_utc <= published_at <= end_utc + timedelta(minutes=5)
