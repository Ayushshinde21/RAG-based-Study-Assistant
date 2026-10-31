import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

import api
import auth_store


class TestAccessControl(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_patch = mock.patch.dict(
            os.environ,
            {
                "AUTH_DB_PATH": str(Path(self.temp_dir.name) / "api-auth.sqlite3"),
                "ADMIN_EMAIL": "admin@example.com",
                "ADMIN_PASSWORD": "unique-admin-password-2026",
                "SESSION_COOKIE_SECURE": "0",
            },
        )
        self.env_patch.start()
        api.LOGIN_ATTEMPTS.clear()
        api.MODEL_REQUESTS.clear()
        auth_store.init_auth_db()
        self.clients = []
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        for client in self.clients:
            client.close()
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def client(self):
        client = TestClient(api.app)
        self.clients.append(client)
        return client

    def signup(self, client, email, name, role):
        response = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "display_name": name,
                "password": "a-strong-password-2026",
                "role": role,
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_farm_tenant_isolation_and_role_guards(self):
        farmer_one = self.client()
        farmer_two = self.client()
        student = self.client()
        admin = self.client()

        one = self.signup(farmer_one, "one@example.com", "Farmer One", "farmer")
        self.signup(farmer_two, "two@example.com", "Farmer Two", "farmer")
        self.signup(student, "student@example.com", "Student", "student")

        create = farmer_one.post(
            "/api/farms",
            json={"name": "My North Field", "soil_moisture": 37.5},
            headers={"X-CSRF-Token": one["csrf_token"]},
        )
        self.assertEqual(create.status_code, 200)
        farm_id = create.json()["id"]

        self.assertEqual(
            [farm["id"] for farm in farmer_one.get("/api/farms").json()],
            [farm_id],
        )
        self.assertEqual(farmer_two.get("/api/farms").json(), [])
        self.assertEqual(farmer_two.get(f"/api/farms/{farm_id}").status_code, 404)
        two_csrf = farmer_two.get("/api/auth/me").json()["csrf_token"]
        self.assertEqual(
            farmer_two.patch(
                f"/api/farms/{farm_id}",
                json={"name": "Unauthorized edit"},
                headers={"X-CSRF-Token": two_csrf},
            ).status_code,
            404,
        )
        self.assertEqual(student.get("/api/farms").status_code, 403)

        admin_login = admin.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "unique-admin-password-2026"},
        )
        self.assertEqual(admin_login.status_code, 200)
        admin_csrf = admin_login.json()["csrf_token"]
        self.assertEqual(admin.get("/api/farms").status_code, 403)
        self.assertEqual(admin.get(f"/api/farms/{farm_id}").status_code, 403)
        self.assertEqual(
            admin.post(
                "/api/farms",
                json={"name": "Admin must not create farms"},
                headers={"X-CSRF-Token": admin_csrf},
            ).status_code,
            403,
        )
        self.assertEqual(
            admin.patch(
                f"/api/farms/{farm_id}",
                json={"name": "Admin must not edit farms"},
                headers={"X-CSRF-Token": admin_csrf},
            ).status_code,
            403,
        )
        self.assertEqual(
            admin.delete(
                f"/api/farms/{farm_id}",
                headers={"X-CSRF-Token": admin_csrf},
            ).status_code,
            403,
        )
        self.assertEqual(admin.get("/api/admin/users").status_code, 200)

    def test_authenticated_mutations_require_csrf(self):
        farmer = self.client()
        self.signup(farmer, "farmer@example.com", "Farmer", "farmer")
        response = farmer.post("/api/farms", json={"name": "No CSRF"})
        self.assertEqual(response.status_code, 403)

    def test_admin_is_not_publicly_registerable(self):
        client = self.client()
        response = client.post(
            "/api/auth/register",
            json={
                "email": "attacker@example.com",
                "display_name": "Attacker",
                "password": "a-strong-password-2026",
                "role": "admin",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_students_only_list_and_open_owned_lectures(self):
        student_one = self.client()
        student_two = self.client()
        admin = self.client()
        one = self.signup(student_one, "lecture-one@example.com", "Student One", "student")
        two = self.signup(student_two, "lecture-two@example.com", "Student Two", "student")

        records = [
            {"id": "owned-one", "title": "Owned one", "owner_user_id": one["user"]["id"], "num_chunks": 1, "created_at": "2026-10-20T10:00:00"},
            {"id": "owned-two", "title": "Owned two", "owner_user_id": two["user"]["id"], "num_chunks": 1, "created_at": "2026-10-20T10:00:00"},
            {"id": "legacy", "title": "Legacy record", "owner_user_id": None, "num_chunks": 1, "created_at": "2026-10-19T10:00:00"},
        ]
        fake_store = type("FakeVectorStore", (), {})()
        fake_store.list_lectures = lambda: records
        fake_store.get_lecture = lambda lecture_id: next(
            (record for record in records if record["id"] == lecture_id), None
        )
        fake_summarizer = type("FakeSummarizer", (), {})()
        fake_summarizer.summarize = lambda docs: "summary for owned lecture"

        with mock.patch.dict(
            sys.modules,
            {
                "core.vector_store": fake_store,
                "features.summarizer": fake_summarizer,
            },
        ), mock.patch.object(api, "get_runtime", return_value={"docs": []}):
            api.SUMMARIES.clear()
            self.assertEqual(
                [item["id"] for item in student_one.get("/api/lectures").json()],
                ["owned-one"],
            )
            self.assertEqual(
                student_one.get("/api/lectures/owned-two/summary").status_code,
                404,
            )
            self.assertEqual(
                student_one.get("/api/lectures/legacy/summary").status_code,
                404,
            )
            self.assertEqual(
                student_one.get("/api/lectures/owned-one/summary").json()["summary"],
                "summary for owned lecture",
            )

            admin_login = admin.post(
                "/api/auth/login",
                json={"email": "admin@example.com", "password": "unique-admin-password-2026"},
            )
            self.assertEqual(admin_login.status_code, 200)
            self.assertEqual(
                {item["id"] for item in admin.get("/api/lectures").json()},
                {"owned-one", "owned-two", "legacy"},
            )

            eval_payload = {
                "items": [{"question": "What is tested?", "ground_truth": "Role access"}]
            }
            student_eval = student_one.post(
                "/api/lectures/owned-one/evaluate",
                json=eval_payload,
                headers={"X-CSRF-Token": one["csrf_token"]},
            )
            self.assertEqual(student_eval.status_code, 403)

            fake_evaluator = type("FakeEvaluator", (), {})()
            fake_evaluator.quick_evaluate = lambda engine, items: {
                "faithfulness": 0.9,
                "answer_relevancy": 0.8,
                "context_precision": 0.85,
                "context_recall": 0.75,
            }
            with mock.patch.dict(sys.modules, {"features.evaluator": fake_evaluator}), \
                 mock.patch.object(api, "get_engine", return_value=object()):
                admin_eval = admin.post(
                    "/api/lectures/owned-one/evaluate",
                    json=eval_payload,
                    headers={"X-CSRF-Token": admin_login.json()["csrf_token"]},
                )
            self.assertEqual(admin_eval.status_code, 200, admin_eval.text)
            self.assertEqual(admin_eval.json()["n"], 1)


if __name__ == "__main__":
    unittest.main()
