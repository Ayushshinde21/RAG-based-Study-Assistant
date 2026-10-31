import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi import HTTPException
from fastapi.testclient import TestClient

import api


class TestSafeErrorHandling(unittest.TestCase):
    def test_unknown_error_does_not_expose_paths_or_secrets(self):
        secret_name = "TEST_PRIVATE_API_KEY"
        secret_value = "secret-value-for-test-only"
        with mock.patch.dict(os.environ, {secret_name: secret_value}):
            message = api.friendly_error(
                RuntimeError(
                    f"failed at C:\\private\\service.py using {secret_value}"
                )
            )

        self.assertNotIn("C:\\private", message)
        self.assertNotIn(secret_value, message)
        self.assertIn("unexpected processing error", message.lower())

    def test_known_user_actionable_error_remains_clear(self):
        message = api.friendly_error(RuntimeError("FFmpeg executable was not found"))
        self.assertIn("FFmpeg", message)
        self.assertNotIn("Traceback", message)


class TestProductionCookieConfiguration(unittest.TestCase):
    def test_production_requires_secure_session_cookie(self):
        with self.assertRaisesRegex(RuntimeError, "SESSION_COOKIE_SECURE=1"):
            api.validate_session_cookie_security("production", False)

    def test_development_can_use_local_http_cookie(self):
        api.validate_session_cookie_security("development", False)

    def test_production_accepts_secure_cookie(self):
        api.validate_session_cookie_security("production", True)


class TestSecurityResponseHeaders(unittest.TestCase):
    def test_api_responses_include_security_headers_and_no_store(self):
        response = TestClient(api.app).get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(response.headers.get("x-frame-options"), "DENY")
        self.assertEqual(
            response.headers.get("referrer-policy"),
            "strict-origin-when-cross-origin",
        )
        self.assertEqual(response.headers.get("cache-control"), "no-store")


class TestAuthenticationRateLimiter(unittest.TestCase):
    def setUp(self):
        self.old_attempts = {key: list(value) for key, value in api.LOGIN_ATTEMPTS.items()}
        api.LOGIN_ATTEMPTS.clear()
        self.limit = api.LOGIN_RATE_LIMIT
        self.window = api.LOGIN_RATE_WINDOW_SECONDS

    def tearDown(self):
        api.LOGIN_ATTEMPTS.clear()
        api.LOGIN_ATTEMPTS.update(self.old_attempts)
        api.LOGIN_RATE_LIMIT = self.limit
        api.LOGIN_RATE_WINDOW_SECONDS = self.window

    def test_authentication_attempts_are_limited_per_client(self):
        api.LOGIN_RATE_LIMIT = 2
        self.assertTrue(api.allow_auth_attempt("192.0.2.10", now=100))
        self.assertTrue(api.allow_auth_attempt("192.0.2.10", now=101))
        self.assertFalse(api.allow_auth_attempt("192.0.2.10", now=102))
        self.assertTrue(api.allow_auth_attempt("192.0.2.11", now=102))

    def test_expired_attempts_are_removed(self):
        api.LOGIN_RATE_LIMIT = 1
        api.LOGIN_RATE_WINDOW_SECONDS = 10
        self.assertTrue(api.allow_auth_attempt("192.0.2.20", now=100))
        self.assertTrue(api.allow_auth_attempt("192.0.2.20", now=111))

    def test_successful_login_can_clear_client_attempts(self):
        self.assertTrue(api.allow_auth_attempt("192.0.2.30", now=100))
        api.clear_auth_attempts("192.0.2.30")
        self.assertNotIn("192.0.2.30", api.LOGIN_ATTEMPTS)




class TestModelRequestRateLimiter(unittest.TestCase):
    def setUp(self):
        self.old_requests = {key: list(value) for key, value in api.MODEL_REQUESTS.items()}
        self.limit = api.MODEL_REQUEST_RATE_LIMIT
        self.window = api.MODEL_REQUEST_WINDOW_SECONDS
        api.MODEL_REQUESTS.clear()

    def tearDown(self):
        api.MODEL_REQUESTS.clear()
        api.MODEL_REQUESTS.update(self.old_requests)
        api.MODEL_REQUEST_RATE_LIMIT = self.limit
        api.MODEL_REQUEST_WINDOW_SECONDS = self.window

    def test_model_requests_are_limited_per_authenticated_user(self):
        api.MODEL_REQUEST_RATE_LIMIT = 2
        api.enforce_model_request_limit(101, now=100)
        api.enforce_model_request_limit(101, now=101)
        with self.assertRaises(HTTPException) as raised:
            api.enforce_model_request_limit(101, now=102)
        self.assertEqual(raised.exception.status_code, 429)
        api.enforce_model_request_limit(202, now=102)

    def test_model_request_limit_resets_after_window(self):
        api.MODEL_REQUEST_RATE_LIMIT = 1
        api.MODEL_REQUEST_WINDOW_SECONDS = 10
        api.enforce_model_request_limit(303, now=100)
        api.enforce_model_request_limit(303, now=111)


class TestProcessingJobLimits(unittest.TestCase):
    def setUp(self):
        self.old_jobs = dict(api.JOBS)
        self.per_user = api.MAX_ACTIVE_JOBS_PER_USER
        self.total = api.MAX_ACTIVE_JOBS_TOTAL
        api.JOBS.clear()

    def tearDown(self):
        api.JOBS.clear()
        api.JOBS.update(self.old_jobs)
        api.MAX_ACTIVE_JOBS_PER_USER = self.per_user
        api.MAX_ACTIVE_JOBS_TOTAL = self.total

    def test_active_jobs_are_limited_per_user(self):
        api.MAX_ACTIVE_JOBS_PER_USER = 1
        first = api.new_job(owner_user_id=51)
        self.assertIn(first, api.JOBS)
        with self.assertRaises(HTTPException) as raised:
            api.new_job(owner_user_id=51)
        self.assertEqual(raised.exception.status_code, 429)
        self.assertEqual(api.new_job(owner_user_id=52) in api.JOBS, True)

    def test_total_active_job_limit_is_enforced(self):
        api.MAX_ACTIVE_JOBS_TOTAL = 1
        api.new_job(owner_user_id=51)
        with self.assertRaises(HTTPException) as raised:
            api.new_job(owner_user_id=52)
        self.assertEqual(raised.exception.status_code, 429)

    def test_completed_jobs_are_pruned_after_retention(self):
        api.JOBS["old-completed"] = {
            "status": "done",
            "finished_at": 1.0,
            "owner_user_id": 51,
        }
        with mock.patch.object(api, "JOB_RETENTION_SECONDS", 3600):
            api.new_job(owner_user_id=52)
        self.assertNotIn("old-completed", api.JOBS)

    def test_rejected_document_job_cleans_temporary_uploads(self):
        api.MAX_ACTIVE_JOBS_PER_USER = 1
        api.new_job(owner_user_id=77)
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_path = Path(temp_dir) / "pending.txt"
            upload_path.write_text("temporary", encoding="utf-8")
            with self.assertRaises(HTTPException):
                api.start_document_job(
                    [{"path": str(upload_path), "filename": "pending.txt"}],
                    owner_user_id=77,
                )
            self.assertFalse(upload_path.exists())

    def test_dead_job_thread_marks_job_as_failed(self):
        class DeadThread:
            def is_alive(self):
                return False

        job_id = api.new_job(owner_user_id=88)
        api.JOBS[job_id]["status"] = "running"
        events = list(api.job_events(job_id, DeadThread()))
        self.assertEqual(len(events), 1)
        self.assertIn('"status": "error"', events[0])
        self.assertEqual(api.JOBS[job_id]["status"], "error")
        self.assertIn("finished_at", api.JOBS[job_id])


if __name__ == "__main__":
    unittest.main()
