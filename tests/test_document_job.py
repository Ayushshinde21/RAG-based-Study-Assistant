import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import api


class FakeDocument:
    def __init__(self, text):
        self.page_content = text
        self.metadata = {"source": "notes.pdf", "chunk_id": 0, "document_chunk": 0}


class FakeVectorStore:
    def __init__(self):
        self.deleted = False

    def delete_collection(self):
        self.deleted = True


class TestStandaloneDocumentJob(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        api.RUNTIME.clear()

    def test_document_job_chunks_indexes_and_registers_uploads(self):
        uploaded_path = Path(self.temp_dir.name) / "notes.pdf"
        uploaded_path.write_bytes(b"temporary upload")
        captured = {}
        fake_store = FakeVectorStore()

        fake_chunker = types.ModuleType("core.chunker")
        fake_chunker.chunk_text = lambda text, source, method: [FakeDocument(text)]

        fake_vector_store = types.ModuleType("core.vector_store")
        fake_vector_store.build_vector_store = lambda docs, reset, collection_name: captured.setdefault("docs", docs) and fake_store
        fake_vector_store.delete_collection = lambda collection_name: None
        fake_vector_store.get_dense_retriever = lambda store, k: ("dense", k)
        fake_vector_store.new_collection_name = lambda: "lecture_document_test"

        def register_lecture(**kwargs):
            captured["registration"] = kwargs
            return "lecture_document_test"

        fake_vector_store.register_lecture = register_lecture

        fake_bm25 = types.ModuleType("core.bm25_index")
        fake_bm25.build_bm25_retriever = lambda docs, k: ("bm25", k)

        job_id = "document-job-test"
        api.JOBS[job_id] = {"status": "queued", "warnings": []}

        with mock.patch.dict(sys.modules, {
            "core.chunker": fake_chunker,
            "core.vector_store": fake_vector_store,
            "core.bm25_index": fake_bm25,
        }), mock.patch.object(api, "extract_reference_text", return_value="[Page 2]\nRegularization reduces overfitting."):
            api.run_document_job(
                job_id,
                [{"path": str(uploaded_path), "filename": "notes.pdf"}],
                owner_user_id=17,
            )

        self.assertEqual(api.JOBS[job_id]["status"], "done")
        self.assertEqual(api.JOBS[job_id]["lecture_id"], "lecture_document_test")
        self.assertFalse(uploaded_path.exists())
        self.assertEqual(captured["registration"]["content_type"], "documents")
        self.assertEqual(captured["registration"]["source_files"], ["notes.pdf"])
        self.assertEqual(captured["registration"]["owner_user_id"], 17)

        indexed_doc = captured["docs"][0]
        self.assertEqual(indexed_doc.metadata["source_type"], "uploaded_document")
        self.assertEqual(indexed_doc.metadata["filename"], "notes.pdf")
        self.assertEqual(indexed_doc.metadata["document_type"], "pdf")
        self.assertEqual(indexed_doc.metadata["document_chunk"], 0)
        self.assertIn("document_id", indexed_doc.metadata)
        self.assertEqual(api.RUNTIME["lecture_document_test"]["docs"], [indexed_doc])

    def test_failed_document_job_cleans_uploaded_file(self):
        uploaded_path = Path(self.temp_dir.name) / "empty.txt"
        uploaded_path.write_bytes(b"temporary upload")
        job_id = "document-job-failure"
        api.JOBS[job_id] = {"status": "queued", "warnings": []}

        fake_chunker = types.ModuleType("core.chunker")
        fake_chunker.chunk_text = lambda text, source, method: []
        with mock.patch.dict(sys.modules, {"core.chunker": fake_chunker}), mock.patch.object(
            api, "extract_reference_text", side_effect=ValueError("No readable text")
        ):
            api.run_document_job(
                job_id,
                [{"path": str(uploaded_path), "filename": "empty.txt"}],
                owner_user_id=18,
            )

        self.assertEqual(api.JOBS[job_id]["status"], "error")
        self.assertIn("No documents could be indexed", api.JOBS[job_id]["error"])
        self.assertFalse(uploaded_path.exists())


if __name__ == "__main__":
    unittest.main()
