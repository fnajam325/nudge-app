import unittest

from nudge import goals
from tests.helpers import NOW, add_goal, add_user, event_names, make_conn


class GoalTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        add_user(self.conn)

    def test_create_goal_tracks_event(self):
        add_goal(self.conn)
        self.assertIn("goal_created", event_names(self.conn, "u1"))

    def test_progress_is_capped_at_100(self):
        add_goal(self.conn, target_cents=1000, saved_cents=2500)
        goal = self.conn.execute("SELECT * FROM goals").fetchone()
        self.assertEqual(goals.progress_pct(goal), 100)

    def test_goal_without_target_shows_zero_progress(self):
        add_goal(self.conn, target_cents=0, saved_cents=500)
        goal = self.conn.execute("SELECT * FROM goals").fetchone()
        self.assertEqual(goals.progress_pct(goal), 0)

    def test_reaching_target_marks_goal_achieved(self):
        add_goal(self.conn, target_cents=1000, saved_cents=1000)
        self.assertEqual(goals.active_goals(self.conn, "u1"), [])
        status = self.conn.execute("SELECT status FROM goals").fetchone()["status"]
        self.assertEqual(status, "achieved")


if __name__ == "__main__":
    unittest.main()
