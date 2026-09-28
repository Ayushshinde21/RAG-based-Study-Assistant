import inspect
import unittest

from langchain_core.documents import Document

from core.hybrid_retriever import reciprocal_rank_fusion
from core.vector_store import build_vector_store


def doc(text):
    return Document(page_content=text)


class TestReciprocalRankFusion(unittest.TestCase):
    def test_doc_in_both_lists_ranks_first(self):
        dense = [doc("a"), doc("shared"), doc("b")]
        bm25 = [doc("c"), doc("shared"), doc("d")]
        merged = reciprocal_rank_fusion(dense, bm25)
        self.assertEqual(merged[0].page_content, "shared")

    def test_duplicates_are_merged(self):
        merged = reciprocal_rank_fusion([doc("x"), doc("y")], [doc("y"), doc("x")])
        self.assertEqual(sorted(d.page_content for d in merged), ["x", "y"])

    def test_empty_inputs(self):
        self.assertEqual(reciprocal_rank_fusion([], []), [])


class TestVectorStoreSignature(unittest.TestCase):
    def test_build_vector_store_accepts_reset(self):
        # app.py calls build_vector_store(docs, reset=True)
        self.assertIn("reset", inspect.signature(build_vector_store).parameters)


if __name__ == "__main__":
    unittest.main()
