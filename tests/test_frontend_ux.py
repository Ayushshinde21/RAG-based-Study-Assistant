import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (PROJECT_ROOT / "frontend" / "script.js").read_text(encoding="utf-8")
STYLES = (PROJECT_ROOT / "frontend" / "style.css").read_text(encoding="utf-8")


class TestFrontendUploadExperience(unittest.TestCase):
    def test_media_documents_and_reference_drop_targets_exist(self):
        self.assertIn('data-drop-target="media"', SCRIPT)
        self.assertIn('data-drop-target="documents"', SCRIPT)
        self.assertIn('data-drop-target="references"', SCRIPT)

    def test_drop_handler_uses_file_transfer_and_change_event(self):
        self.assertIn("const assignDroppedFiles = (input, files)", SCRIPT)
        self.assertIn("new DataTransfer()", SCRIPT)
        self.assertIn('new Event("change", { bubbles: true })', SCRIPT)

    def test_dropped_media_and_documents_are_validated(self):
        self.assertIn('new Set(["mp4", "mkv", "avi", "mov", "webm", "mp3", "wav", "m4a", "ogg", "flac"])', SCRIPT)
        self.assertIn('new Set(["pdf", "docx", "pptx", "txt", "md"])', SCRIPT)

    def test_upload_progress_is_accessible(self):
        self.assertIn('role="progressbar"', SCRIPT)
        self.assertIn('aria-valuemin="0"', SCRIPT)
        self.assertIn('aria-valuemax="100"', SCRIPT)
        self.assertIn('setAttribute("aria-valuenow"', SCRIPT)
        self.assertIn('setAttribute("aria-busy"', SCRIPT)


class TestFrontendChatExperience(unittest.TestCase):
    def test_source_passages_can_be_copied(self):
        self.assertIn('class="source-copy-button" data-copy-source=', SCRIPT)
        self.assertIn('closest("[data-copy-source]")', SCRIPT)
        self.assertIn('"Source passage copied"', SCRIPT)

    def test_question_character_counter_is_present_and_updated(self):
        self.assertIn('id="questionCounter"', SCRIPT)
        self.assertIn("const updateQuestionCounter = () =>", SCRIPT)
        self.assertIn("${input.value.length} / 2000", SCRIPT)

    def test_workspace_tabs_support_keyboard_navigation(self):
        self.assertIn('role="tabpanel" tabindex="0"', SCRIPT)
        self.assertIn('aria-controls="tab"', SCRIPT)
        self.assertIn('event.key === "ArrowRight"', SCRIPT)
        self.assertIn('event.key === "ArrowLeft"', SCRIPT)
        self.assertIn('event.key === "Home"', SCRIPT)
        self.assertIn('event.key === "End"', SCRIPT)

    def test_focus_and_drag_states_have_visible_styles(self):
        self.assertIn('[data-drop-target].is-dragover', STYLES)
        self.assertIn('.source-copy-button:focus-visible', STYLES)
        self.assertIn('@media (prefers-reduced-motion: reduce)', STYLES)


if __name__ == "__main__":
    unittest.main()
