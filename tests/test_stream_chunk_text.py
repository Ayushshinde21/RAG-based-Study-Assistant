import unittest
from types import SimpleNamespace

from core.llm import stream_chunk_text


class TestStreamingChunkWhitespace(unittest.TestCase):
    def test_preserves_leading_spaces_between_chunks(self):
        chunks = [SimpleNamespace(content="The"), SimpleNamespace(content=" main"), SimpleNamespace(content=" idea") ]
        combined = "".join(stream_chunk_text(chunk) for chunk in chunks)
        self.assertEqual(combined, "The main idea")

    def test_preserves_whitespace_only_chunks(self):
        self.assertEqual(stream_chunk_text(SimpleNamespace(content=" ")), " ")

    def test_preserves_text_blocks_in_list_content(self):
        chunk = SimpleNamespace(content=[
            {"type": "text", "text": "Direct"},
            {"type": "text", "text": " answer"},
        ])
        self.assertEqual(stream_chunk_text(chunk), "Direct answer")


if __name__ == "__main__":
    unittest.main()
