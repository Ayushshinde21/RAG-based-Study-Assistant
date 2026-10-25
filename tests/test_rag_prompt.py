import unittest

from langchain_core.documents import Document

from core.rag_engine import build_prompt


class TestStructuredChatPrompt(unittest.TestCase):
    def test_prompt_requires_structured_markdown(self):
        prompt = build_prompt("Explain binary tree traversal", [], "")
        self.assertIn("clean Markdown", prompt)
        self.assertIn("## Explanation", prompt)
        self.assertIn("numbered steps", prompt)
        self.assertIn("Markdown table", prompt)

    def test_prompt_preserves_grounding_and_supplied_timestamps(self):
        docs = [Document(
            page_content="Inorder traversal visits left subtree, root, then right subtree.",
            metadata={"start_time_str": "04:12"},
        )]
        prompt = build_prompt("What is inorder traversal?", docs, "Student: Explain traversal\n")
        self.assertIn("[Chunk 1 — around 04:12]", prompt)
        self.assertIn("left subtree, root, then right subtree", prompt)
        self.assertIn("Student: Explain traversal", prompt)
        self.assertIn("I could not find this in the lecture.", prompt)

    def test_empty_retrieval_is_explicit(self):
        prompt = build_prompt("What is quantum computing?", [], "")
        self.assertIn("No lecture excerpts were retrieved.", prompt)


if __name__ == "__main__":
    unittest.main()
