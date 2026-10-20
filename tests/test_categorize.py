import unittest

from nudge.timeutil import days_ago
from nudge.transactions.categorize import categorize, categorize_pending, uncategorized_share
from tests.helpers import NOW, add_account, add_txn, add_user, make_conn


class CategorizeTests(unittest.TestCase):
    def test_known_merchant_matches_case_insensitively(self):
        self.assertEqual(categorize("WHOLE FOODS MKT #123"), "groceries")

    def test_unknown_merchant_stays_uncategorized(self):
        self.assertIsNone(categorize("Joe's Corner Deli"))

    def test_categorize_pending_only_assigns_matches(self):
        conn = make_conn()
        add_user(conn)
        acct = add_account(conn)
        add_txn(conn, "t1", "u1", acct, 1, -2000, "Starbucks")
        add_txn(conn, "t2", "u1", acct, 1, -2000, "Joe's Corner Deli")
        self.assertEqual(categorize_pending(conn), 1)
        cats = {r["id"]: r["category"] for r in conn.execute("SELECT id, category FROM transactions")}
        self.assertEqual(cats, {"t1": "dining", "t2": None})

    def test_uncategorized_share(self):
        conn = make_conn()
        add_user(conn)
        acct = add_account(conn)
        add_txn(conn, "t1", "u1", acct, 1, -2000, "Starbucks", "dining")
        add_txn(conn, "t2", "u1", acct, 1, -2000, "Joe's Corner Deli")
        add_txn(conn, "t3", "u1", acct, 1, 90000, "Payroll", "income")  # income is not spending
        self.assertEqual(uncategorized_share(conn, "u1", days_ago(NOW, 30)), 0.5)

    def test_uncategorized_share_is_zero_without_spending(self):
        conn = make_conn()
        add_user(conn)
        self.assertEqual(uncategorized_share(conn, "u1", days_ago(NOW, 30)), 0.0)


if __name__ == "__main__":
    unittest.main()
