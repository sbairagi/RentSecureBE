from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from django.utils import timezone as dj_timezone


def utc_now() -> datetime:
    return dj_timezone.now()


def today_utc() -> date:
    return dj_timezone.now().date()


def to_utc(value: datetime) -> datetime:
    if dj_timezone.is_naive(value):
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def from_utc(value: datetime, tz_name: str) -> datetime:
    if tz_name.lower() == "utc":
        return value
    return value.astimezone(ZoneInfo(tz_name))


__all__ = [
    "utc_now",
    "today_utc",
    "to_utc",
    "from_utc",
]
