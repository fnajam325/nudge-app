import unittest

from nudge.analytics import track
from nudge.seed import seed_demo
from tests.helpers import NOW, add_user, make_conn


class AnalyticsTests(unittest.TestCase):
    def test_unknown_event_names_are_rejected(self):
        conn = make_conn()
        add_user(conn)
        with self.assertRaises(ValueError):
            track(conn, "u1", "made_up_event", NOW)


class SeedTests(unittest.TestCase):
    def test_seed_is_deterministic(self):
        a, b = make_conn(), make_conn()
        self.assertEqual(seed_demo(a, NOW, n_users=30), seed_demo(b, NOW, n_users=30))

    def test_seed_loads_a_mix_of_users(self):
        conn = make_conn()
        summary = seed_demo(conn, NOW, n_users=60)
        self.assertEqual(summary["users"], 60)
        self.assertTrue(0 < summary["goal_setters"] < 60)
        self.assertTrue(0 < summary["savings_account_holders"] < 60)


if __name__ == "__main__":
    unittest.main()
