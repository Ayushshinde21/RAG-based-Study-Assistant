import tempfile
import unittest
from pathlib import Path
from unittest import mock
from zipfile import ZipFile

from utils.document_reader import DocumentReadError, read_document_text


class TestOfficeArchiveSecurity(unittest.TestCase):
    def test_rejects_non_zip_docx_before_parsing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "fake.docx"
            path.write_text("not a zip archive", encoding="utf-8")
            with self.assertRaisesRegex(DocumentReadError, "valid DOCX/PPTX archive"):
                read_document_text(str(path), "fake.docx")

    def test_rejects_oversized_expanded_archive_member(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "oversized.docx"
            with ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", "x" * 32)

            with mock.patch("utils.document_reader.MAX_OFFICE_MEMBER_BYTES", 16):
                with self.assertRaisesRegex(DocumentReadError, "oversized embedded file"):
                    read_document_text(str(path), "oversized.docx")

    def test_rejects_archive_with_too_many_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "many_entries.pptx"
            with ZipFile(path, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", "one")
                archive.writestr("ppt/slides/slide2.xml", "two")

            with mock.patch("utils.document_reader.MAX_OFFICE_ARCHIVE_ENTRIES", 1):
                with self.assertRaisesRegex(DocumentReadError, "too many archive entries"):
                    read_document_text(str(path), "many_entries.pptx")

    def test_rejects_archive_over_total_expansion_limit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "large.pptx"
            with ZipFile(path, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", "a" * 12)
                archive.writestr("ppt/slides/slide2.xml", "b" * 12)

            with mock.patch("utils.document_reader.MAX_OFFICE_MEMBER_BYTES", 20), \
                 mock.patch("utils.document_reader.MAX_OFFICE_UNCOMPRESSED_BYTES", 20):
                with self.assertRaisesRegex(DocumentReadError, "allowed processing size"):
                    read_document_text(str(path), "large.pptx")


if __name__ == "__main__":
    unittest.main()
