import importlib
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

import numpy as np


class _FakeWhisperModel:
    def transcribe(self, audio, **kwargs):
        return iter([]), types.SimpleNamespace(language="en")


class TestLongVideoProcessing(unittest.TestCase):
    def setUp(self):
        fake_whisper = types.ModuleType("faster_whisper")
        fake_whisper.WhisperModel = lambda *args, **kwargs: _FakeWhisperModel()
        with mock.patch.dict(sys.modules, {"faster_whisper": fake_whisper}):
            sys.modules.pop("utils.transcriber", None)
            self.transcriber = importlib.import_module("utils.transcriber")
        self.addCleanup(lambda: sys.modules.pop("utils.transcriber", None))

    def test_english_windows_keep_absolute_timestamps_and_report_progress(self):
        progress = []
        mocked_segments = [
            [{"start": 1.0, "end": 2.0, "text": "first"}],
            [{"start": 3.0, "end": 4.0, "text": "second"}],
            [{"start": 5.0, "end": 6.0, "text": "third"}],
        ]
        with mock.patch.dict(os.environ, {"WHISPER_CHUNK_SECONDS": "300"}), \
             mock.patch.object(self.transcriber, "_split_audio", return_value=["p1", "p2", "p3"]), \
             mock.patch.object(self.transcriber, "transcribe_english_segments", side_effect=mocked_segments):
            result = self.transcriber._transcribe_english_in_chunks("long.mp3", 650, progress.append)

        self.assertEqual([item["start"] for item in result], [1.0, 303.0, 605.0])
        self.assertEqual([item["text"] for item in result], ["first", "second", "third"])
        self.assertEqual(len(progress), 3)
        self.assertIn("1 of 3", progress[0])
        self.assertIn("3 of 3", progress[-1])

    def test_long_transcription_detects_language_from_sample_not_full_audio(self):
        with tempfile.NamedTemporaryFile(suffix=".mp3") as audio_file, \
             mock.patch.object(self.transcriber, "_get_audio_duration", return_value=10800), \
             mock.patch.object(self.transcriber, "load_audio_window", return_value=np.ones(16000, dtype=np.float32)), \
             mock.patch.object(self.transcriber, "detect_language", return_value="en"), \
             mock.patch.object(self.transcriber, "load_audio", side_effect=AssertionError("whole-file audio should not be loaded")), \
             mock.patch.object(self.transcriber, "_transcribe_english_in_chunks", return_value=[{"start": 0, "end": 1, "text": "ok"}]) as chunks:
            result = self.transcriber.transcribe_with_timestamps(audio_file.name)

        self.assertEqual(result[0]["text"], "ok")
        chunks.assert_called_once()
        self.assertEqual(chunks.call_args.args[1], 10800)

    def test_caption_parser_preserves_timestamps_and_cleans_markup(self):
        fake_yt_dlp = types.ModuleType("yt_dlp")
        fake_yt_dlp.utils = types.SimpleNamespace(DownloadError=Exception)
        fake_yt_dlp.YoutubeDL = object
        with mock.patch.dict(sys.modules, {"yt_dlp": fake_yt_dlp}):
            sys.modules.pop("utils.audio_processor", None)
            audio_processor = importlib.import_module("utils.audio_processor")

        self.addCleanup(lambda: sys.modules.pop("utils.audio_processor", None))
        with tempfile.NamedTemporaryFile("w", suffix=".vtt", encoding="utf-8", delete=False) as handle:
            handle.write("WEBVTT\n\n00:00:01.000 --> 00:00:03.500 align:start\n<c>Welcome</c> &amp; hello\n\n00:00:03.500 --> 00:00:05.000\nNext part\n")
            path = handle.name
        try:
            result = audio_processor.parse_caption_file(path)
        finally:
            os.remove(path)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["start"], 1.0)
        self.assertEqual(result[0]["end"], 3.5)
        self.assertEqual(result[0]["text"], "Welcome & hello")


if __name__ == "__main__":
    unittest.main()
