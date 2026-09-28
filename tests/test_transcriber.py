import os
import sys
import tempfile
import types
import unittest
from unittest import mock


def seg(text):
    return types.SimpleNamespace(text=text)


class FakeModel:
    """Stands in for faster_whisper.WhisperModel so no model is downloaded."""

    def __init__(self, language, texts):
        self.language = language
        self.texts = texts
        self.calls = []

    def transcribe(self, path, **kwargs):
        self.calls.append(kwargs)
        info = types.SimpleNamespace(language=self.language)
        return iter(seg(t) for t in self.texts), info


class TestTranscribeRouting(unittest.TestCase):
    def setUp(self):
        fake_fw = types.ModuleType("faster_whisper")
        fake_fw.WhisperModel = lambda *a, **k: FakeModel("en", [])
        patcher = mock.patch.dict(sys.modules, {"faster_whisper": fake_fw})
        patcher.start()
        self.addCleanup(patcher.stop)
        sys.modules.pop("utils.transcriber", None)
        import utils.transcriber as t
        self.t = t
        self.addCleanup(lambda: sys.modules.pop("utils.transcriber", None))
        self.audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        self.audio.close()
        self.addCleanup(os.remove, self.audio.name)

    def test_english_uses_single_whisper_call(self):
        self.t.model = FakeModel("en", [" hello", " world "])
        self.assertEqual(self.t.transcribe(self.audio.name), "hello  world")
        self.assertEqual(len(self.t.model.calls), 1)

    def test_hindi_goes_to_sarvam_path(self):
        self.t.model = FakeModel("hi", [])
        with mock.patch.object(self.t, "transcribe_hindi", return_value="translated") as hi:
            self.assertEqual(self.t.transcribe(self.audio.name), "translated")
        hi.assert_called_once_with(self.audio.name)

    def test_other_language_falls_back_to_forced_english(self):
        self.t.model = FakeModel("fr", [])
        with mock.patch.object(self.t, "transcribe_english", return_value="fr->en") as en:
            self.assertEqual(self.t.transcribe(self.audio.name), "fr->en")
        en.assert_called_once_with(self.audio.name)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.t.transcribe("does_not_exist.mp3")


if __name__ == "__main__":
    unittest.main()
