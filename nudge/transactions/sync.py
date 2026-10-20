"""Pull transactions and balances from the aggregator. Run nightly (see nudge/jobs.py)."""
from __future__ import annotations

from datetime import datetime, timedelta

from .. import config
from ..timeutil import iso, parse, start_of_day
from .providers import Provider, ProviderError


def sync_account(conn, account, provider: Provider, now: datetime) -> int:
    """Sync one account. Returns the number of new transactions stored."""
    # Re-read from the start of the last sync day. Inserts are idempotent by transaction id,
    # so the overlap is harmless and avoids losing late-visible transactions.
    since = iso(start_of_day(parse(account["last_synced_at"]))) if account["last_synced_at"] else None
    snapshot = provider.fetch_account(account["id"], since, now)
    inserted = 0
    for t in snapshot["transactions"]:
        cur = conn.execute(
            "INSERT OR IGNORE INTO transactions (id, account_id, user_id, posted_at, amount_cents, merchant) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (t["id"], account["id"], account["user_id"], t["posted_at"], t["amount_cents"], t["merchant"]),
        )
        inserted += cur.rowcount
    conn.execute(
        "UPDATE accounts SET balance_cents = ?, last_synced_at = ? WHERE id = ?",
        (snapshot["balance_cents"], iso(now), account["id"]),
    )
    conn.commit()
    return inserted


def sync_all(conn, provider: Provider, now: datetime) -> dict:
    """Sync every linked account. One account failing does not stop the rest."""
    summary = {"accounts": 0, "new_transactions": 0, "failed": []}
    for account in conn.execute("SELECT * FROM accounts ORDER BY id").fetchall():
        try:
            summary["new_transactions"] += sync_account(conn, account, provider, now)
            summary["accounts"] += 1
        except ProviderError:
            summary["failed"].append(account["id"])
    return summary


def is_stale(account, now: datetime) -> bool:
    if not account["last_synced_at"]:
        return True
    return parse(account["last_synced_at"]) < now - timedelta(hours=config.SYNC_STALE_AFTER_HOURS)
