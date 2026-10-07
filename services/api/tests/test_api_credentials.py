import unittest
from datetime import datetime, timedelta, timezone

from app.api_credentials import API_CLIENT_ROLES, new_api_token, token_digest, is_expired


class ApiCredentialTests(unittest.TestCase):
    def test_tokens_are_random_prefixed_and_only_store_a_digest(self):
        first, second = new_api_token(), new_api_token()
        self.assertTrue(first.startswith("nxo_live_"))
        self.assertNotEqual(first, second)
        digest = token_digest(first)
        self.assertEqual(len(digest), 64)
        self.assertNotIn(first, digest)

    def test_api_roles_exclude_workspace_and_hr_privileged_roles(self):
        self.assertEqual(API_CLIENT_ROLES, {"Sales", "Purchasing", "Warehouse", "Finance manager"})
        self.assertNotIn("Owner", API_CLIENT_ROLES)
        self.assertNotIn("HR manager", API_CLIENT_ROLES)

    def test_expiry_boundary_is_closed(self):
        now = datetime(2026, 10, 7, tzinfo=timezone.utc)
        self.assertFalse(is_expired(now + timedelta(seconds=1), now))
        self.assertTrue(is_expired(now, now))
        self.assertTrue(is_expired(now - timedelta(seconds=1), now))


if __name__ == "__main__":
    unittest.main()
