"""Time helpers. Everything is stored as UTC ISO-8601 strings, e.g. 2026-02-02T15:00:00Z."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

FMT = "%Y-%m-%dT%H:%M:%SZ"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime(FMT)


def parse(value: str) -> datetime:
    return datetime.strptime(value, FMT).replace(tzinfo=timezone.utc)


def days_ago(now: datetime, days: int) -> str:
    return iso(now - timedelta(days=days))


def start_of_day(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
