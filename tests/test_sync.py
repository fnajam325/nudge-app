import unittest
from datetime import timedelta

from nudge.timeutil import iso
from nudge.transactions.providers import FakeProvider
from nudge.transactions.sync import is_stale, sync_account, sync_all
from tests.helpers import NOW, add_account, add_user, make_conn


def txn(txn_id, posted_at, amount=-1000):
    return {"id": txn_id, "posted_at": iso(posted_at), "amount_cents": amount, "merchant": "Starbucks"}


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        add_user(self.conn)
        self.acct = add_account(self.conn)
        self.provider = FakeProvider()

    def _account(self):
        return self.conn.execute("SELECT * FROM accounts WHERE id = ?", (self.acct,)).fetchone()

    def test_sync_stores_transactions_and_balance(self):
        self.provider.add(self.acct, 123_00, [txn("t1", NOW - timedelta(days=2))])
        self.assertEqual(sync_account(self.conn, self._account(), self.provider, NOW), 1)
        self.assertEqual(self._account()["balance_cents"], 123_00)
        self.assertIsNotNone(self._account()["last_synced_at"])

    def test_todays_transactions_are_not_visible_yet(self):
        self.provider.add(self.acct, 0, [txn("t1", NOW - timedelta(hours=3))])
        self.assertEqual(sync_account(self.conn, self._account(), self.provider, NOW), 0)

    def test_sync_is_idempotent(self):
        self.provider.add(self.acct, 0, [txn("t1", NOW - timedelta(days=2))])
        sync_account(self.conn, self._account(), self.provider, NOW)
        self.assertEqual(sync_account(self.conn, self._account(), self.provider, NOW + timedelta(days=1)), 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0], 1)

    def test_late_visible_transaction_is_picked_up_next_night(self):
        night_one = NOW.replace(hour=4)
        posted = night_one - timedelta(hours=2)  # posted on night one's day, becomes visible the next day
        self.provider.add(self.acct, 0, [txn("t1", posted)])
        self.assertEqual(sync_account(self.conn, self._account(), self.provider, night_one), 0)
        self.assertEqual(sync_account(self.conn, self._account(), self.provider, night_one + timedelta(days=1)), 1)

    def test_one_failing_account_does_not_stop_the_rest(self):
        add_user(self.conn, "u2")
        other = add_account(self.conn, "u2")
        self.provider.add(self.acct, 0, [])
        self.provider.add(other, 0, [txn("t9", NOW - timedelta(days=2))])
        self.provider.fail(self.acct)
        summary = sync_all(self.conn, self.provider, NOW)
        self.assertEqual(summary["failed"], [self.acct])
        self.assertEqual(summary["new_transactions"], 1)

    def test_staleness(self):
        self.assertTrue(is_stale(self._account(), NOW))  # never synced
        self.provider.add(self.acct, 0, [])
        sync_account(self.conn, self._account(), self.provider, NOW)
        self.assertFalse(is_stale(self._account(), NOW + timedelta(hours=12)))
        self.assertTrue(is_stale(self._account(), NOW + timedelta(hours=48)))


if __name__ == "__main__":
    unittest.main()
