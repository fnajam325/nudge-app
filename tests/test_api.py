import unittest
from datetime import timedelta

from nudge.api import handlers
from nudge.notifications import scheduler
from nudge.notifications.sender import LoggingPushProvider
from tests.helpers import NOW, add_user, event_names, make_conn


class HandlerTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        add_user(self.conn)

    def test_get_home_returns_cards_and_marks_the_user_active(self):
        later = NOW + timedelta(days=2)
        result = handlers.get_home(self.conn, "u1", later)
        self.assertEqual(result["cards"][0]["type"], "goals")
        active = self.conn.execute("SELECT last_active_at FROM users").fetchone()["last_active_at"]
        self.assertEqual(active, "2026-02-04T15:00:00Z")

    def test_post_goal_creates_a_goal(self):
        result = handlers.post_goal(self.conn, "u1", {"name": " vacation ", "target_cents": 250_000}, NOW)
        self.assertEqual(result["name"], "vacation")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM goals").fetchone()[0], 1)

    def test_post_goal_requires_a_name(self):
        with self.assertRaises(ValueError):
            handlers.post_goal(self.conn, "u1", {"name": "  "}, NOW)

    def test_server_side_events_are_rejected_from_clients(self):
        with self.assertRaises(ValueError):
            handlers.post_client_event(self.conn, "u1", {"name": "nudge_sent"}, NOW)

    def test_client_nudge_open_updates_the_nudge(self):
        (sent,) = scheduler.run(self.conn, NOW, LoggingPushProvider())
        handlers.post_client_event(self.conn, "u1", {"name": "nudge_opened", "properties": {"nudge_id": sent["nudge_id"]}}, NOW)
        self.assertIsNotNone(self.conn.execute("SELECT opened_at FROM nudges").fetchone()["opened_at"])

    def test_session_ended_keeps_screen_and_duration(self):
        body = {"name": "session_ended", "properties": {"screen": "home", "duration_seconds": 92}}
        handlers.post_client_event(self.conn, "u1", body, NOW)
        row = self.conn.execute("SELECT properties FROM events WHERE name = 'session_ended'").fetchone()
        self.assertEqual(row["properties"], '{"duration_seconds": 92, "screen": "home"}')
        self.assertIn("session_ended", event_names(self.conn, "u1"))


if __name__ == "__main__":
    unittest.main()
