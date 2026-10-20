"""Deterministic demo data for local exploration. Not used in production."""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from . import accounts, goals, users
from .timeutil import iso
from .transactions.categorize import categorize_pending

KNOWN_MERCHANTS = [
    "Whole Foods", "Trader Joe's", "Starbucks", "Chipotle", "Uber", "Netflix", "Spotify", "Amazon", "Shell", "Comcast",
]
UNKNOWN_MERCHANTS = [
    "Joe's Corner Deli", "Mercado La Esperanza", "City Parking 44", "Dr. Patel DDS", "Blue Door Books", "Lakeview Dry Cleaning",
]
GOAL_NAMES = ["emergency fund", "vacation", "new laptop", "down payment", "wedding"]


def seed_demo(conn, now: datetime, n_users: int = 120, seed: int = 7) -> dict:
    rng = random.Random(seed)
    txn_id = 0
    goal_setters = savings_holders = 0
    for i in range(1, n_users + 1):
        uid = f"u{i:04d}"
        signup = now - timedelta(days=rng.randint(2, 40), hours=rng.randint(0, 23))
        users.create_user(
            conn,
            uid,
            signup,
            platform=rng.choice(["ios", "ios", "android"]),
            channel=rng.choice(["organic", "organic", "paid", "referral"]),
            push_opt_in=rng.random() < 0.85,
        )
        last_active = max(signup, now - timedelta(days=rng.randint(0, 20)))
        conn.execute("UPDATE users SET last_active_at = ? WHERE id = ?", (iso(last_active), uid))

        has_goal = rng.random() < 0.33
        has_savings = rng.random() < (0.52 if has_goal else 0.48)
        checking = f"a{i:04d}c"
        accounts.link_account(conn, checking, uid, "checking", "First Fictional Bank", signup)
        account_ids = [checking]
        if has_savings:
            savings = f"a{i:04d}s"
            accounts.link_account(conn, savings, uid, "savings", "First Fictional Bank", signup)
            account_ids.append(savings)
            savings_holders += 1
        for account_id in account_ids:
            conn.execute(
                "UPDATE accounts SET balance_cents = ?, last_synced_at = ? WHERE id = ?",
                (rng.randint(20_000, 900_000), iso(now - timedelta(hours=rng.randint(2, 30))), account_id),
            )

        if has_goal:
            goal_setters += 1
            created = min(now, signup + timedelta(days=rng.randint(0, 6)))
            target = rng.choice([50_000, 150_000, 300_000, 500_000])
            goals.create_goal(conn, f"g{i:04d}", uid, rng.choice(GOAL_NAMES), target, created)
            goals.record_saving(conn, f"g{i:04d}", int(target * rng.choice([0, 0.1, 0.3, 0.55, 0.8, 1.0])))

        window = max(1, (now - timedelta(days=1) - signup).days)
        for _ in range(rng.randint(12, 45)):
            txn_id += 1
            posted = now - timedelta(days=rng.randint(1, window), hours=rng.randint(0, 23))
            merchant = rng.choice(KNOWN_MERCHANTS if rng.random() < 0.7 else UNKNOWN_MERCHANTS)
            conn.execute(
                "INSERT INTO transactions (id, account_id, user_id, posted_at, amount_cents, merchant) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (f"t{txn_id:06d}", checking, uid, iso(posted), -rng.randint(300, 12_000), merchant),
            )
    conn.commit()
    categorize_pending(conn, limit=1_000_000)
    return {
        "users": n_users,
        "goal_setters": goal_setters,
        "savings_account_holders": savings_holders,
        "transactions": txn_id,
    }
