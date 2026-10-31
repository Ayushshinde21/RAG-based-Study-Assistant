import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import auth_store


class TestAuthStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_patch = mock.patch.dict(
            os.environ,
            {
                "AUTH_DB_PATH": str(Path(self.temp_dir.name) / "auth-test.sqlite3"),
                "ADMIN_EMAIL": "",
                "ADMIN_PASSWORD": "",
            },
        )
        self.env_patch.start()
        self.addCleanup(self._cleanup)
        auth_store.init_auth_db()

    def _cleanup(self):
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def test_password_hash_and_session(self):
        user = auth_store.create_user(
            "student@example.com", "Sample Student", "long-password-123", "student"
        )
        self.assertEqual(user["role"], "student")
        self.assertEqual(
            auth_store.authenticate_user("student@example.com", "long-password-123")["id"],
            user["id"],
        )
        self.assertIsNone(
            auth_store.authenticate_user("student@example.com", "incorrect-password")
        )
        token, csrf = auth_store.create_session(user["id"])
        session = auth_store.get_session(token)
        self.assertEqual(session["user"]["id"], user["id"])
        self.assertEqual(session["csrf_token"], csrf)
        auth_store.revoke_session(token)
        self.assertIsNone(auth_store.get_session(token))

    def test_farmer_records_are_filterable_by_owner(self):
        one = auth_store.create_user("farmer1@example.com", "Farmer One", "long-password-123", "farmer")
        two = auth_store.create_user("farmer2@example.com", "Farmer Two", "long-password-456", "farmer")
        first_farm = auth_store.create_farm(one["id"], {"name": "Farm Alpha", "soil_moisture": 42.5})
        second_farm = auth_store.create_farm(two["id"], {"name": "Farm Beta", "temperature_c": 28})
        self.assertEqual(
            [farm["id"] for farm in auth_store.list_farms(one["id"])],
            [first_farm["id"]],
        )
        self.assertEqual(
            [farm["id"] for farm in auth_store.list_farms(two["id"])],
            [second_farm["id"]],
        )
        self.assertEqual(len(auth_store.list_farms()), 2)
        self.assertIsNone(
            auth_store.update_farm(second_farm["id"], one["id"], {"name": "Intrusion"})
        )
        self.assertFalse(auth_store.delete_farm(second_farm["id"], one["id"]))
        self.assertEqual(auth_store.get_farm(second_farm["id"])["name"], "Farm Beta")

    def test_admin_bootstrap_and_disable_revokes_session(self):
        os.environ["ADMIN_EMAIL"] = "admin@example.com"
        os.environ["ADMIN_PASSWORD"] = "a-unique-admin-password"
        auth_store.init_auth_db()
        admin = auth_store.authenticate_user("admin@example.com", "a-unique-admin-password")
        self.assertEqual(admin["role"], "admin")
        token, _ = auth_store.create_session(admin["id"])
        self.assertTrue(auth_store.set_user_active(admin["id"], False))
        self.assertIsNone(auth_store.get_session(token))

    def test_admin_bootstrap_is_safe_when_account_already_exists(self):
        os.environ["ADMIN_EMAIL"] = "admin@example.com"
        os.environ["ADMIN_PASSWORD"] = "a-unique-admin-password"
        auth_store.init_auth_db()
        auth_store.init_auth_db()
        admin = auth_store.authenticate_user("admin@example.com", "a-unique-admin-password")
        self.assertIsNotNone(admin)
        self.assertEqual(admin["role"], "admin")


if __name__ == "__main__":
    unittest.main()
