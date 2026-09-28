"""Tests for core/chunker.py — fixed-size chunking (no embedding model needed,
unlike chunk_semantic, so these run without downloading anything)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.chunker import chunk_fixed, chunk_text


class TestChunkFixed(unittest.TestCase):
    def test_short_text_single_chunk(self):
        text = "This is a short sentence about linear algebra."
        docs = chunk_fixed(text, source="test.txt", chunk_size=500, overlap=50)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].page_content, text)
        self.assertEqual(docs[0].metadata["source"], "test.txt")
        self.assertEqual(docs[0].metadata["method"], "fixed")

    def test_long_text_multiple_chunks_with_sequential_ids(self):
        text = "A matrix is a rectangular array of numbers. " * 100
        docs = chunk_fixed(text, source="lecture.txt", chunk_size=500, overlap=50)
        self.assertGreater(len(docs), 1)
        chunk_ids = [d.metadata["chunk_id"] for d in docs]
        self.assertEqual(chunk_ids, list(range(len(docs))))

    def test_no_empty_chunks(self):
        text = "Word. " * 300
        docs = chunk_fixed(text, chunk_size=500, overlap=50)
        self.assertTrue(all(d.page_content.strip() for d in docs))


class TestChunkText(unittest.TestCase):
    def test_empty_text_raises(self):
        with self.assertRaises(ValueError):
            chunk_text("   ", method="fixed")

    def test_unknown_method_raises(self):
        with self.assertRaises(ValueError):
            chunk_text("Some text here.", method="not_a_real_method")

    def test_fixed_method_delegates_to_chunk_fixed(self):
        text = "Vectors and matrices. " * 50
        docs = chunk_text(text, source="x.txt", method="fixed")
        self.assertGreaterEqual(len(docs), 1)
        self.assertEqual(docs[0].metadata["method"], "fixed")


if __name__ == "__main__":
    unittest.main()
