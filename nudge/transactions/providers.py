"""Bank aggregator interface plus an in-memory stand-in.

The real aggregator client lives in the core-banking service. What matters here is its one
relevant quirk (docs/adr/0002-nightly-transaction-sync.md): a transaction only becomes
visible the day after it posts.
"""
from __future__ import annotations

from datetime import datetime
from typing import Protocol

from ..timeutil import iso, start_of_day


class ProviderError(Exception):
    pass


class Provider(Protocol):
    def fetch_account(self, account_id: str, since: str | None, now: datetime) -> dict:
        """Return {"balance_cents": int, "transactions": [dict]} for transactions
        posted on or after `since` and before the start of today (UTC)."""


class FakeProvider:
    def __init__(self) -> None:
        self._accounts: dict[str, dict] = {}
        self._failing: set[str] = set()

    def add(self, account_id: str, balance_cents: int, transactions: list[dict]) -> None:
        self._accounts[account_id] = {"balance_cents": balance_cents, "transactions": transactions}

    def fail(self, account_id: str) -> None:
        self._failing.add(account_id)

    def fetch_account(self, account_id: str, since: str | None, now: datetime) -> dict:
        if account_id in self._failing:
            raise ProviderError(f"aggregator timeout for {account_id}")
        snapshot = self._accounts[account_id]
        visible_before = iso(start_of_day(now))
        txns = [
            t
            for t in snapshot["transactions"]
            if t["posted_at"] < visible_before and (since is None or t["posted_at"] >= since)
        ]
        return {"balance_cents": snapshot["balance_cents"], "transactions": txns}
