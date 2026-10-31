import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SESSION_COOKIE_SECURE", "0")
os.environ.setdefault("AUTH_DB_PATH", str(Path(tempfile.gettempdir()) / "test-document-upload.sqlite3"))

from fastapi import HTTPException
from fastapi.testclient import TestClient
import api


class TestDocumentUploadRoute(unittest.TestCase):
    def test_document_upload_requires_authentication(self):
        client = TestClient(api.app)
        response = client.post(
            "/api/lectures/documents",
            files=[("files", ("notes.txt", b"A document about RAG.", "text/plain"))],
        )
        self.assertEqual(response.status_code, 401)

    def test_document_upload_rejects_empty_file_list(self):
        with self.assertRaises(HTTPException) as raised:
            api.upload_documents(files=[], user={"id": 1, "role": "student"})
        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("at least one document", raised.exception.detail.lower())

    def test_document_upload_starts_authenticated_job(self):
        from unittest import mock

        uploaded = type("Upload", (), {"filename": "notes.pdf"})()
        saved_files = [{"path": "temporary-notes", "filename": "notes.pdf"}]
        fake_thread = object()
        with mock.patch.object(api, "_save_reference_uploads", return_value=saved_files) as save_files, \
             mock.patch.object(api, "start_document_job", return_value=("job-123", fake_thread)) as start_job, \
             mock.patch.object(api, "job_events", return_value=iter([])):
            response = api.upload_documents(files=[uploaded], user={"id": 42, "role": "student"})

        self.assertEqual(response.media_type, "application/x-ndjson")
        save_files.assert_called_once_with(
            [uploaded],
            max_files=api.MAX_DOCUMENT_FILES,
            max_file_mb=api.MAX_DOCUMENT_FILE_MB,
            file_label="document",
        )
        start_job.assert_called_once_with(saved_files, 42)


if __name__ == "__main__":
    unittest.main()
