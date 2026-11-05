import os
import unittest
from unittest import mock

from storage.database import database_backend, postgres_enabled, connect_postgres


class TestDatabaseBackendSelection(unittest.TestCase):
    def test_auto_uses_sqlite_without_postgres_configuration(self):
        with mock.patch.dict(os.environ, {"DATABASE_BACKEND": "auto"}, clear=True):
            self.assertEqual(database_backend(), "sqlite")
            self.assertFalse(postgres_enabled())

    def test_auto_uses_postgres_with_connection_url(self):
        with mock.patch.dict(
            os.environ,
            {"DATABASE_BACKEND": "auto", "DATABASE_URL": "postgresql://user:pass@localhost/db"},
            clear=True,
        ):
            self.assertEqual(database_backend(), "postgres")
            self.assertTrue(postgres_enabled())

    def test_auto_uses_postgres_with_cloud_sql_fields(self):
        with mock.patch.dict(
            os.environ,
            {"DATABASE_BACKEND": "auto", "DB_USER": "user", "DB_PASSWORD": "secret", "DB_NAME": "db"},
            clear=True,
        ):
            self.assertEqual(database_backend(), "postgres")

    def test_invalid_backend_is_rejected(self):
        with mock.patch.dict(os.environ, {"DATABASE_BACKEND": "mysql"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "DATABASE_BACKEND"):
                database_backend()

    def test_missing_postgres_credentials_fail_clearly(self):
        with mock.patch.dict(os.environ, {"DATABASE_BACKEND": "postgres"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "Set DATABASE_URL"):
                connect_postgres()


if __name__ == "__main__":
    unittest.main()
