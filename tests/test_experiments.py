import unittest
from unittest import mock

from nudge.experiments import EXPERIMENTS, get_variant
from nudge.experiments.assignment import bucket
from nudge.experiments.registry import Experiment
from tests.helpers import NOW, add_user, event_names, make_conn


class AssignmentTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()

    def test_bucket_is_stable_and_in_range(self):
        self.assertEqual(bucket("u1", "exp"), bucket("u1", "exp"))
        self.assertTrue(all(0 <= bucket(f"u{i}", "exp") < 100 for i in range(200)))

    def test_assignment_is_sticky(self):
        add_user(self.conn)
        first = get_variant(self.conn, "u1", "weekly_tip_copy", NOW)
        self.assertIn(first, ("control", "short"))
        self.assertEqual(get_variant(self.conn, "u1", "weekly_tip_copy", NOW), first)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM experiment_assignments").fetchone()[0], 1)

    def test_assignment_is_logged_when_made_not_when_seen(self):
        add_user(self.conn)
        get_variant(self.conn, "u1", "weekly_tip_copy", NOW)
        get_variant(self.conn, "u1", "weekly_tip_copy", NOW)
        self.assertEqual(event_names(self.conn, "u1").count("experiment_assigned"), 1)

    def test_users_outside_traffic_are_not_enrolled(self):
        add_user(self.conn)
        half = Experiment("half", ("a", "b"), traffic_pct=0, started_at="2025-01-01T00:00:00Z")
        with mock.patch.dict(EXPERIMENTS, {"half": half}):
            self.assertIsNone(get_variant(self.conn, "u1", "half", NOW))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM experiment_assignments").fetchone()[0], 0)

    def test_concluded_experiment_enrolls_nobody_new(self):
        add_user(self.conn)
        self.assertIsNone(get_variant(self.conn, "u1", "onboarding_checklist_v2", NOW))

    def test_new_users_only_skips_users_created_before_start(self):
        add_user(self.conn, days_old=400)
        exp = Experiment("new_only", ("a", "b"), 100, started_at="2026-01-01T00:00:00Z", new_users_only=True)
        with mock.patch.dict(EXPERIMENTS, {"new_only": exp}):
            self.assertIsNone(get_variant(self.conn, "u1", "new_only", NOW))

    def test_split_is_roughly_even(self):
        for i in range(400):
            add_user(self.conn, f"u{i}")
        counts = {"control": 0, "short": 0}
        for i in range(400):
            counts[get_variant(self.conn, f"u{i}", "weekly_tip_copy", NOW)] += 1
        self.assertTrue(150 < counts["control"] < 250, counts)


if __name__ == "__main__":
    unittest.main()
