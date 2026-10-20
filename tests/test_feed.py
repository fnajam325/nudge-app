import unittest

from nudge import config, users
from nudge.feed import compose_home_feed
from tests.helpers import NOW, add_account, add_goal, add_txn, add_user, event_names, make_conn


def types(feed):
    return [c["type"] for c in feed]


class HomeFeedTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()

    def _feed(self, user_id):
        return compose_home_feed(self.conn, users.get_user(self.conn, user_id), NOW)

    def test_new_user_with_nothing_linked_sees_only_the_goal_prompt(self):
        add_user(self.conn, days_old=0)
        feed = self._feed("u1")
        self.assertEqual(types(feed), ["goals"])
        self.assertEqual(feed[0]["cta"], "Set a savings goal")

    def test_every_user_gets_the_same_card_order(self):
        for uid in ("u1", "u2"):
            add_user(self.conn, uid)
            acct = add_account(self.conn, uid)
            add_txn(self.conn, f"t-{uid}", uid, acct, 2, -1500, "Starbucks", "dining")
        add_goal(self.conn, "u2")
        self.assertEqual(types(self._feed("u1")), config.HOME_FEED_ORDER)
        self.assertEqual(types(self._feed("u2")), config.HOME_FEED_ORDER)

    def test_uncategorized_spending_is_grouped_and_labelled(self):
        add_user(self.conn)
        acct = add_account(self.conn)
        add_txn(self.conn, "t1", "u1", acct, 2, -4000, "Joe's Corner Deli")
        card = next(c for c in self._feed("u1") if c["type"] == "spending_by_category")
        self.assertEqual(card["categories"][0]["category"], "uncategorized")

    def test_balance_card_flags_stale_data(self):
        add_user(self.conn)
        add_account(self.conn)
        card = next(c for c in self._feed("u1") if c["type"] == "balance")
        self.assertTrue(card["stale"])  # never synced

    def test_viewing_the_feed_records_only_a_card_count(self):
        add_user(self.conn)
        self._feed("u1")
        row = self.conn.execute("SELECT properties FROM events WHERE name = 'feed_viewed'").fetchone()
        self.assertEqual(row["properties"], '{"card_count": 1}')
        self.assertIn("feed_viewed", event_names(self.conn, "u1"))


if __name__ == "__main__":
    unittest.main()
