import os
import sys
import tempfile
import types
import unittest
from unittest import mock

import numpy as np


class FakeModel:
    """Stands in for faster_whisper.WhisperModel so no model is downloaded."""

    def transcribe(self, audio, **kwargs):
        return iter([]), types.SimpleNamespace(language="en")


class TestTranscribeRouting(unittest.TestCase):
    def setUp(self):
        fake_fw = types.ModuleType("faster_whisper")
        fake_fw.WhisperModel = lambda *a, **k: FakeModel()
        patcher = mock.patch.dict(sys.modules, {"faster_whisper": fake_fw})
        patcher.start()
        self.addCleanup(patcher.stop)
        sys.modules.pop("utils.transcriber", None)
        import utils.transcriber as t
        self.t = t
        self.addCleanup(lambda: sys.modules.pop("utils.transcriber", None))
        self.audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        self.audio.close()
        self.addCleanup(lambda: os.path.exists(self.audio.name) and os.remove(self.audio.name))

    def test_plain_transcribe_joins_timestamped_text(self):
        with mock.patch.object(self.t, "transcribe_with_timestamps", return_value=[
            {"start": 0, "end": 1, "text": "hello"},
            {"start": 1, "end": 2, "text": "world"},
        ]):
            self.assertEqual(self.t.transcribe(self.audio.name), "hello world")

    def test_hindi_uses_sarvam_path(self):
        with mock.patch.object(self.t, "_get_audio_duration", return_value=60), \
             mock.patch.object(self.t, "load_audio_window", return_value=np.ones(16000, dtype=np.float32)), \
             mock.patch.object(self.t, "detect_language", return_value="hi"), \
             mock.patch.object(self.t, "transcribe_hindi_segments", return_value=[{"start": 0, "end": 20, "text": "translated"}]) as hindi:
            result = self.t.transcribe_with_timestamps(self.audio.name)
        self.assertEqual(result[0]["text"], "translated")
        hindi.assert_called_once_with(self.audio.name, progress_callback=None)

    def test_other_language_uses_chunked_english_fallback(self):
        expected = [{"start": 0, "end": 1, "text": "translated to English"}]
        with mock.patch.object(self.t, "_get_audio_duration", return_value=720), \
             mock.patch.object(self.t, "load_audio_window", return_value=np.ones(16000, dtype=np.float32)), \
             mock.patch.object(self.t, "detect_language", return_value="fr"), \
             mock.patch.object(self.t, "_transcribe_english_in_chunks", return_value=expected) as english:
            result = self.t.transcribe_with_timestamps(self.audio.name)
        self.assertEqual(result, expected)
        english.assert_called_once_with(self.audio.name, 720, None)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.t.transcribe("does_not_exist.mp3")

    def test_silent_sample_raises(self):
        with mock.patch.object(self.t, "_get_audio_duration", return_value=10), \
             mock.patch.object(self.t, "load_audio_window", return_value=np.zeros(16000, dtype=np.float32)):
            with self.assertRaisesRegex(RuntimeError, "sampled audio appears silent"):
                self.t.transcribe_with_timestamps(self.audio.name)


if __name__ == "__main__":
    unittest.main()
