import sys
import types
import unittest
from unittest import mock

import api
from fastapi import HTTPException
from pydantic import ValidationError


class FakeEngine:
    def __init__(self, dense, bm25):
        self.dense = dense
        self.bm25 = bm25

    def prepare_stream(self, query, preferences=None):
        return iter(["answer"]), [], lambda _answer: None


class TestApiSessionIsolation(unittest.TestCase):
    def setUp(self):
        self.original_engines = dict(api.ENGINES)
        api.ENGINES.clear()

    def tearDown(self):
        api.ENGINES.clear()
        api.ENGINES.update(self.original_engines)

    def test_chat_engines_are_isolated_between_users(self):
        fake_module = types.ModuleType("core.rag_engine")
        fake_module.RAGEngine = FakeEngine
        runtime = {"dense": object(), "bm25": object()}

        with mock.patch.dict(sys.modules, {"core.rag_engine": fake_module}), \
             mock.patch.object(api, "get_runtime", return_value=runtime):
            first = api.get_engine("lecture-1", "browser-session", 101)
            first_again = api.get_engine("lecture-1", "browser-session", 101)
            second_user = api.get_engine("lecture-1", "browser-session", 202)

        self.assertIs(first, first_again)
        self.assertIsNot(first, second_user)
        self.assertIn(("lecture-1", 101, "browser-session"), api.ENGINES)
        self.assertIn(("lecture-1", 202, "browser-session"), api.ENGINES)

    def test_chat_route_uses_authenticated_user_id_for_engine_scope(self):
        captured = {}

        def fake_get_engine(lecture_id, session_id, user_id):
            captured["key"] = (lecture_id, session_id, user_id)
            return FakeEngine(None, None)

        request = api.ChatRequest(
            question="  Explain RAG  ",
            session_id="browser-session",
        )

        with mock.patch.object(api, "require_lecture_access"), \
             mock.patch.object(api, "get_engine", side_effect=fake_get_engine):
            response = api.chat(
                "lecture-1",
                request,
                user={"id": 303, "role": "student"},
            )

        self.assertEqual(captured["key"], ("lecture-1", "browser-session", 303))
        self.assertEqual(response.media_type, "application/x-ndjson")

    def test_reset_chat_removes_only_calling_users_session(self):
        first_engine = object()
        second_engine = object()
        api.ENGINES[("lecture-1", 101, "browser-session")] = first_engine
        api.ENGINES[("lecture-1", 202, "browser-session")] = second_engine

        with mock.patch.object(api, "require_lecture_access"):
            result = api.reset_chat(
                "lecture-1",
                "browser-session",
                user={"id": 101, "role": "student"},
            )

        self.assertEqual(result, {"reset": True})
        self.assertNotIn(("lecture-1", 101, "browser-session"), api.ENGINES)
        self.assertIs(api.ENGINES[("lecture-1", 202, "browser-session")], second_engine)


class TestApiRequestValidation(unittest.TestCase):
    def test_chat_question_is_trimmed(self):
        request = api.ChatRequest(question="  What is RAG?  ")
        self.assertEqual(request.question, "What is RAG?")

    def test_chat_rejects_whitespace_only_question(self):
        with self.assertRaises(ValidationError):
            api.ChatRequest(question="   \n  ")

    def test_chat_rejects_invalid_session_id_characters(self):
        with self.assertRaises(ValidationError):
            api.ChatRequest(question="What is RAG?", session_id="session id/unsafe")

    def test_chat_accepts_frontend_session_id(self):
        request = api.ChatRequest(
            question="What is RAG?",
            session_id="a1b2c3d4e5f6",
        )
        self.assertEqual(request.session_id, "a1b2c3d4e5f6")

    def test_evaluation_items_reject_blank_question_or_reference(self):
        with self.assertRaises(ValidationError):
            api.EvalItem(question="  ", ground_truth="Expected answer")
        with self.assertRaises(ValidationError):
            api.EvalItem(question="Question", ground_truth="  ")

    def test_evaluation_text_is_trimmed(self):
        item = api.EvalItem(
            question="  What is RAG?  ",
            ground_truth="  Retrieval augmented generation.  ",
        )
        self.assertEqual(item.question, "What is RAG?")
        self.assertEqual(item.ground_truth, "Retrieval augmented generation.")


class TestJobStatusAccess(unittest.TestCase):
    def setUp(self):
        self.previous = api.JOBS.get("job-private-test")
        api.JOBS["job-private-test"] = {
            "status": "done",
            "stage": "Workspace ready",
            "step": 4,
            "total": 4,
            "lecture_id": "lecture-private",
            "error": None,
            "warnings": [],
            "owner_user_id": 101,
        }

    def tearDown(self):
        api.JOBS.pop("job-private-test", None)
        if self.previous is not None:
            api.JOBS["job-private-test"] = self.previous

    def test_job_status_is_hidden_from_other_users(self):
        with self.assertRaises(HTTPException) as caught:
            api.job_status(
                "job-private-test",
                user={"id": 202, "role": "student"},
            )
        self.assertEqual(caught.exception.status_code, 404)

    def test_job_status_hides_owner_user_id_from_response(self):
        result = api.job_status(
            "job-private-test",
            user={"id": 101, "role": "student"},
        )
        self.assertEqual(result["status"], "done")
        self.assertEqual(result["lecture_id"], "lecture-private")
        self.assertNotIn("owner_user_id", result)


if __name__ == "__main__":
    unittest.main()
