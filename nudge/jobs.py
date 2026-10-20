"""Scheduled jobs. Production cron: nightly_sync at 04:00 UTC, hourly_notifications at the top of every hour."""
from __future__ import annotations

from datetime import datetime

from .notifications import scheduler
from .notifications.sender import PushProvider
from .transactions.categorize import categorize_pending
from .transactions.providers import Provider
from .transactions.sync import sync_all


def nightly_sync(conn, provider: Provider, now: datetime) -> dict:
    summary = sync_all(conn, provider, now)
    summary["categorized"] = categorize_pending(conn)
    return summary


def hourly_notifications(conn, push: PushProvider, now: datetime) -> list[dict]:
    return scheduler.run(conn, now, push)
