import unittest

from nudge import users
from nudge.notifications import frequency
from tests.helpers import NOW, add_nudge, add_user, make_conn


class FrequencyCapTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        add_user(self.conn)

    def _can_send(self):
        return frequency.can_send(self.conn, users.get_user(self.conn, "u1"), NOW)

    def test_under_the_cap_can_send(self):
        add_nudge(self.conn, "u1", "weekly_tip", days_ago=3)
        self.assertTrue(self._can_send())

    def test_cap_is_global_across_nudge_types(self):
        add_nudge(self.conn, "u1", "weekly_tip", days_ago=1)
        add_nudge(self.conn, "u1", "spending_alert", days_ago=2)
        self.assertFalse(self._can_send())

    def test_nudges_older_than_a_week_do_not_count(self):
        add_nudge(self.conn, "u1", "weekly_tip", days_ago=8)
        add_nudge(self.conn, "u1", "spending_alert", days_ago=9)
        self.assertTrue(self._can_send())

    def test_failed_sends_do_not_count(self):
        add_nudge(self.conn, "u1", "weekly_tip", days_ago=1, status="failed")
        add_nudge(self.conn, "u1", "spending_alert", days_ago=2, status="failed")
        self.assertTrue(self._can_send())

    def test_opted_out_users_never_receive_pushes(self):
        self.conn.execute("UPDATE users SET push_opt_in = 0 WHERE id = 'u1'")
        self.assertFalse(self._can_send())


if __name__ == "__main__":
    unittest.main()
