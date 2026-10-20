"""Rules-based merchant categorization. A merchant that matches no rule stays uncategorized."""
from __future__ import annotations

MERCHANT_RULES: dict[str, list[str]] = {
    "groceries": ["whole foods", "trader joe", "kroger", "safeway", "aldi", "costco"],
    "dining": ["starbucks", "chipotle", "mcdonald", "doordash", "uber eats", "blue bottle"],
    "transport": ["uber", "lyft", "shell", "chevron", "mta", "bart"],
    "subscriptions": ["netflix", "spotify", "hulu", "apple.com/bill"],
    "utilities": ["comcast", "verizon", "pg&e", "con edison"],
    "shopping": ["amazon", "target", "walmart"],
    "income": ["payroll", "direct dep"],
}


def categorize(merchant: str) -> str | None:
    name = merchant.lower()
    for category, needles in MERCHANT_RULES.items():
        if any(needle in name for needle in needles):
            return category
    return None


def categorize_pending(conn, limit: int = 5000) -> int:
    """Categorize transactions that have no category yet. Returns how many were assigned one."""
    rows = conn.execute(
        "SELECT id, merchant FROM transactions WHERE category IS NULL LIMIT ?", (limit,)
    ).fetchall()
    assigned = 0
    for row in rows:
        category = categorize(row["merchant"])
        if category:
            conn.execute("UPDATE transactions SET category = ? WHERE id = ?", (category, row["id"]))
            assigned += 1
    conn.commit()
    return assigned


def uncategorized_share(conn, user_id: str, since: str) -> float:
    """Share of a user's spending transactions since `since` with no category (0.0 when there are none)."""
    row = conn.execute(
        "SELECT COUNT(*) AS total, SUM(category IS NULL) AS missing FROM transactions "
        "WHERE user_id = ? AND amount_cents < 0 AND posted_at >= ?",
        (user_id, since),
    ).fetchone()
    return (row["missing"] or 0) / row["total"] if row["total"] else 0.0
