from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from django.utils import timezone as dj_timezone

from core.shared.time import from_utc, to_utc, today_utc, utc_now


class TestSharedTime:
    def test_utc_now_returns_aware_datetime(self):
        result = utc_now()
        assert isinstance(result, datetime)
        assert dj_timezone.is_aware(result)

    def test_utc_now_timezone_is_utc(self):
        result = utc_now()
        assert result.tzinfo is not None
        assert result.utcoffset() == UTC.utcoffset(None)

    def test_today_utc_returns_date(self):
        result = today_utc()
        assert isinstance(result, date)

    def test_today_utc_matches_utc_now(self):
        assert today_utc() == utc_now().date()

    def test_to_utc_naive_datetime(self):
        naive = datetime(2024, 1, 1, 12, 0, 0)
        result = to_utc(naive)
        assert dj_timezone.is_aware(result)
        assert result.utcoffset() == UTC.utcoffset(None)

    def test_to_utc_already_aware(self):
        aware = dj_timezone.make_aware(datetime(2024, 1, 1, 12, 0, 0))
        result = to_utc(aware)
        assert dj_timezone.is_aware(result)

    def test_from_utc_to_timezone(self):
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        result = from_utc(dt, "Asia/Kolkata")
        expected = dt.astimezone(ZoneInfo("Asia/Kolkata"))
        assert result == expected

    def test_from_utc_utc_returns_same(self):
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        result = from_utc(dt, "utc")
        assert result == dt
