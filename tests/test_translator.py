import unittest

from utils.translator import _split_text


class TestSplitText(unittest.TestCase):
    def test_short_text_is_single_chunk(self):
        self.assertEqual(_split_text("hello world", max_length=1000), ["hello world"])

    def test_chunks_respect_max_length(self):
        text = " ".join(["This is a sentence."] * 200)
        chunks = _split_text(text, max_length=100)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(c) <= 100 for c in chunks))

    def test_no_words_lost(self):
        text = " ".join(f"word{i}." for i in range(300))
        chunks = _split_text(text, max_length=120)
        self.assertEqual(" ".join(chunks).split(), text.split())

    def test_splits_on_hindi_full_stop(self):
        text = ("यह एक वाक्य है। " * 30).strip()
        chunks = _split_text(text, max_length=60)
        self.assertTrue(all(c.endswith("।") for c in chunks))


if __name__ == "__main__":
    unittest.main()
