import json
import unittest
from datetime import timedelta

from nudge.notifications import selector
from nudge.timeutil import iso
from tests.helpers import NOW, add_account, add_goal, add_nudge, add_txn, add_user, make_conn


def ids(candidates):
    return [c.user_id for c in candidates]


class GoalReminderTests(unittest.TestCase):
    def test_candidates_are_savings_account_holders(self):
        conn = make_conn()
        add_user(conn, "u1")
        add_account(conn, "u1", "savings")
        add_user(conn, "u2")
        add_account(conn, "u2", "checking")
        self.assertEqual(ids(selector.select(conn, "goal_reminder", NOW)), ["u1"])

    def test_goal_name_is_used_when_the_user_has_a_goal(self):
        conn = make_conn()
        add_user(conn)
        add_account(conn, "u1", "savings")
        add_goal(conn, "u1", name="vacation")
        self.assertEqual(selector.select(conn, "goal_reminder", NOW)[0].context, {"goal_name": "vacation"})

    def test_not_repeated_within_a_week(self):
        conn = make_conn()
        add_user(conn)
        add_account(conn, "u1", "savings")
        add_nudge(conn, "u1", "goal_reminder", days_ago=3)
        self.assertEqual(selector.select(conn, "goal_reminder", NOW), [])


class MilestoneTests(unittest.TestCase):
    def test_crossing_a_threshold_selects_the_user(self):
        conn = make_conn()
        add_user(conn)
        add_goal(conn, "u1", target_cents=100_000, saved_cents=55_000)
        (cand,) = selector.select(conn, "milestone", NOW)
        self.assertEqual(cand.context["threshold"], 50)

    def test_same_threshold_is_not_sent_twice(self):
        conn = make_conn()
        add_user(conn)
        goal_id = add_goal(conn, "u1", target_cents=100_000, saved_cents=55_000)
        add_nudge(conn, "u1", "milestone", days_ago=1, payload=json.dumps({"goal_id": goal_id, "threshold": 50}))
        self.assertEqual(selector.select(conn, "milestone", NOW), [])

    def test_goal_without_target_is_ignored(self):
        conn = make_conn()
        add_user(conn)
        add_goal(conn, "u1", target_cents=0, saved_cents=5_000)
        self.assertEqual(selector.select(conn, "milestone", NOW), [])


class ReEngagementTests(unittest.TestCase):
    def _set_last_active(self, conn, user_id, days):
        conn.execute("UPDATE users SET last_active_at = ? WHERE id = ?", (iso(NOW - timedelta(days=days)), user_id))
        conn.commit()

    def test_window_is_three_to_thirty_days_inactive(self):
        conn = make_conn()
        for uid, days in [("u1", 1), ("u2", 4), ("u3", 45)]:
            add_user(conn, uid)
            self._set_last_active(conn, uid, days)
        self.assertEqual(ids(selector.select(conn, "re_engagement", NOW)), ["u2"])


class SpendingAlertTests(unittest.TestCase):
    def test_week_over_week_spike_in_a_known_category(self):
        conn = make_conn()
        add_user(conn)
        acct = add_account(conn)
        add_txn(conn, "t1", "u1", acct, 10, -5_000, category="groceries")  # prior week
        add_txn(conn, "t2", "u1", acct, 2, -20_000, category="groceries")  # this week
        (cand,) = selector.select(conn, "spending_alert", NOW)
        self.assertEqual(cand.context, {"category": "groceries"})

    def test_uncategorized_spending_never_triggers_an_alert(self):
        conn = make_conn()
        add_user(conn)
        acct = add_account(conn)
        add_txn(conn, "t1", "u1", acct, 2, -90_000)
        self.assertEqual(selector.select(conn, "spending_alert", NOW), [])

    def test_small_amounts_are_ignored(self):
        conn = make_conn()
        add_user(conn)
        acct = add_account(conn)
        add_txn(conn, "t1", "u1", acct, 2, -4_000, category="dining")
        self.assertEqual(selector.select(conn, "spending_alert", NOW), [])


class WeeklyTipTests(unittest.TestCase):
    def test_brand_new_users_wait_a_day(self):
        conn = make_conn()
        add_user(conn, "old", days_old=10)
        add_user(conn, "new", days_old=0)
        self.assertEqual(ids(selector.select(conn, "weekly_tip", NOW)), ["old"])

    def test_opted_out_users_are_excluded(self):
        conn = make_conn()
        add_user(conn, "u1", push_opt_in=False)
        self.assertEqual(selector.select(conn, "weekly_tip", NOW), [])


if __name__ == "__main__":
    unittest.main()
