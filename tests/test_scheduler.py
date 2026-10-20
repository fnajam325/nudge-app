import unittest
from datetime import timedelta

from nudge.notifications import engagement, scheduler
from nudge.notifications.sender import LoggingPushProvider
from tests.helpers import NOW, add_account, add_nudge, add_txn, add_user, event_names, make_conn


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.push = LoggingPushProvider()

    def test_nothing_is_sent_outside_the_send_hour(self):
        add_user(self.conn)
        self.assertEqual(scheduler.run(self.conn, NOW.replace(hour=9), self.push), [])
        self.assertEqual(self.push.sent, [])

    def test_sends_and_records_a_nudge(self):
        add_user(self.conn)
        (result,) = scheduler.run(self.conn, NOW, self.push)
        self.assertEqual(result["nudge_type"], "weekly_tip")
        self.assertEqual(len(self.push.sent), 1)
        self.assertIn("nudge_sent", event_names(self.conn, "u1"))

    def test_one_nudge_per_user_per_run_highest_priority_wins(self):
        add_user(self.conn)
        acct = add_account(self.conn)
        add_account(self.conn, account_type="savings")
        add_txn(self.conn, "t1", "u1", acct, 2, -30_000, category="shopping")
        (result,) = scheduler.run(self.conn, NOW, self.push)
        self.assertEqual(result["nudge_type"], "spending_alert")

    def test_the_global_cap_blocks_a_third_push_in_a_week(self):
        add_user(self.conn)
        add_nudge(self.conn, "u1", "milestone", days_ago=1)
        add_nudge(self.conn, "u1", "re_engagement", days_ago=2)
        self.assertEqual(scheduler.run(self.conn, NOW, self.push), [])

    def test_failed_push_is_recorded_but_not_counted_as_sent(self):
        add_user(self.conn)
        self.push.failing_users.add("u1")
        self.assertEqual(scheduler.run(self.conn, NOW, self.push), [])
        status = self.conn.execute("SELECT status FROM nudges").fetchone()["status"]
        self.assertEqual(status, "failed")
        self.assertNotIn("nudge_sent", event_names(self.conn, "u1"))

    def test_running_twice_in_the_same_hour_does_not_double_send(self):
        add_user(self.conn)
        scheduler.run(self.conn, NOW, self.push)
        self.assertEqual(scheduler.run(self.conn, NOW + timedelta(minutes=5), self.push), [])

    def test_the_send_hour_is_utc_for_every_user(self):
        add_user(self.conn, "east", timezone="America/New_York")
        add_user(self.conn, "tokyo", timezone="Asia/Tokyo")
        results = scheduler.run(self.conn, NOW, self.push)
        self.assertEqual({r["user_id"] for r in results}, {"east", "tokyo"})


class EngagementTests(unittest.TestCase):
    def test_open_and_action_are_recorded(self):
        conn = make_conn()
        add_user(conn)
        (result,) = scheduler.run(conn, NOW, LoggingPushProvider())
        engagement.mark_opened(conn, result["nudge_id"], NOW + timedelta(hours=1))
        engagement.mark_acted_on(conn, result["nudge_id"], NOW + timedelta(hours=1))
        row = conn.execute("SELECT opened_at, acted_on_at FROM nudges").fetchone()
        self.assertIsNotNone(row["opened_at"])
        self.assertIsNotNone(row["acted_on_at"])
        names = event_names(conn, "u1")
        self.assertIn("nudge_opened", names)
        self.assertIn("nudge_acted_on", names)

    def test_unknown_nudge_raises(self):
        conn = make_conn()
        with self.assertRaises(KeyError):
            engagement.mark_opened(conn, "nope", NOW)


if __name__ == "__main__":
    unittest.main()
