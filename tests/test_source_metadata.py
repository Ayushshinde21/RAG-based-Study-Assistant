import unittest

from langchain_core.documents import Document

from api import source_payload
from core.chunker import _extract_start_time, chunk_fixed


class TestStructuredSourceMetadata(unittest.TestCase):
    def test_pdf_page_markers_become_page_metadata(self):
        text = (
            "[Page 2]\n"
            + ("Information from page two. " * 12)
            + "\n\n[Page 5]\n"
            + ("Information from page five. " * 12)
        )

        docs = chunk_fixed(text, source="lecture_notes.pdf", chunk_size=90, overlap=10)

        self.assertTrue(docs)
        page_two_docs = [doc for doc in docs if doc.metadata.get("page_number") == 2]
        page_five_docs = [doc for doc in docs if doc.metadata.get("page_number") == 5]
        self.assertTrue(page_two_docs)
        self.assertTrue(page_five_docs)
        self.assertTrue(all("[Page " not in doc.page_content for doc in docs))
        self.assertTrue(all(doc.metadata["filename"] == "lecture_notes.pdf" for doc in docs))

    def test_powerpoint_slide_markers_become_slide_metadata(self):
        text = (
            "[Slide 1]\nFirst slide content.\n\n"
            "[Slide 4]\nFourth slide content."
        )

        docs = chunk_fixed(text, source="lecture_slides.pptx", chunk_size=500, overlap=20)

        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0].metadata.get("slide_number"), 1)
        self.assertEqual(docs[1].metadata.get("slide_number"), 4)
        self.assertNotIn("[Slide", docs[0].page_content)

    def test_fixed_chunking_preserves_transcript_timestamp_metadata(self):
        docs = chunk_fixed(
            "[00:35] First transcript segment.\n[01:10] Second transcript segment.",
            source="lecture.txt",
            chunk_size=500,
            overlap=20,
        )
        self.assertEqual(docs[0].metadata.get("start_time_str"), "00:35")

    def test_transcript_timestamp_parser_supports_minute_and_hour_formats(self):
        self.assertEqual(_extract_start_time("[05:20] Transcript text"), "05:20")
        self.assertEqual(_extract_start_time("[1:05:20] Transcript text"), "1:05:20")
        self.assertIsNone(_extract_start_time("Transcript without timestamp"))

    def test_api_source_payload_preserves_provenance(self):
        docs = [
            Document(
                page_content="Regularization reduces overfitting.",
                metadata={
                    "source": "regularization.pdf",
                    "filename": "regularization.pdf",
                    "source_type": "lecturer_material",
                    "page_number": 12,
                    "chunk_id": 3,
                    "document_chunk": 3,
                },
            ),
            Document(
                page_content="The lecturer explains the next topic.",
                metadata={
                    "source": "lecture_transcript.txt",
                    "source_type": "lecture_transcript",
                    "start_time_str": "04:12",
                    "chunk_id": 5,
                },
            ),
        ]

        payload = source_payload(docs)

        self.assertEqual(payload[0]["filename"], "regularization.pdf")
        self.assertEqual(payload[0]["source_type"], "lecturer_material")
        self.assertEqual(payload[0]["page_number"], 12)
        self.assertEqual(payload[0]["chunk_id"], 3)
        self.assertEqual(payload[1]["time"], "04:12")
        self.assertEqual(payload[1]["source_type"], "lecture_transcript")
        self.assertEqual(payload[1]["filename"], "lecture_transcript.txt")

    def test_api_source_payload_reads_legacy_location_markers(self):
        doc = Document(
            page_content="[Page 8]\nLegacy PDF passage [04:12]",
            metadata={"source": "legacy.pdf"},
        )

        payload = source_payload([doc])

        self.assertEqual(payload[0]["page_number"], 8)
        self.assertEqual(payload[0]["time"], "04:12")
        self.assertEqual(payload[0]["filename"], "legacy.pdf")

    def test_uploaded_audio_video_title_uses_original_filename(self):
        from api import uploaded_lecture_title

        self.assertEqual(
            uploaded_lecture_title(r"C:\fakepath\Computer_Networks_Lecture_01.mp4"),
            "Computer_Networks_Lecture_01",
        )
        self.assertEqual(uploaded_lecture_title("lecture.wav"), "lecture")
        self.assertEqual(uploaded_lecture_title(None), "Uploaded lecture")

    def test_api_source_payload_keeps_legacy_time_and_text_fields(self):
        doc = Document(
            page_content="A timestamped lecture passage.",
            metadata={"start_time_str": "02:30"},
        )

        payload = source_payload([doc])

        self.assertEqual(payload[0]["text"], "A timestamped lecture passage.")
        self.assertEqual(payload[0]["time"], "02:30")


if __name__ == "__main__":
    unittest.main()
