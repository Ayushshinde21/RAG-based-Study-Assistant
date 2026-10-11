"""
utils/pdf_reader.py

Reads a PDF (lecture notes, slides, textbook chapter) and turns it into plain
text that the existing pipeline can chunk and index, exactly like a transcript.

Typical use in app.py (same flow as audio):

    from utils.pdf_reader import pdf_to_transcript_file
    transcript_path = pdf_to_transcript_file(tmp_path)
    docs = chunk_from_file(transcript_path, method="semantic")

Requires:  pip install pypdf   (add `pypdf` to requirements.txt)
"""

import os
import re
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

TRANSCRIPT_DIR = "transcripts"


class PDFReadError(RuntimeError):
    """Raised when a PDF can't be read or contains no extractable text."""


def _clean_text(text: str) -> str:
    """Fix common PDF extraction artefacts without changing the meaning."""
    # Re-join words split by a line-break hyphen: "algo-\nrithm" -> "algorithm"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Single newlines inside a paragraph -> space; keep blank lines as breaks
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # Collapse runs of spaces/tabs and excessive blank lines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_pdf_pages(pdf_path: str) -> list[dict]:
    """
    Extract text page by page.
    Returns a list of {"page": 1-based page number, "text": cleaned text}.
    Pages with no extractable text are skipped.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        reader = PdfReader(str(path))
    except PdfReadError as e:
        raise PDFReadError(f"Could not open PDF (corrupt or unsupported): {e}") from e

    if reader.is_encrypted:
        # Many "protected" PDFs only have an owner password; an empty user
        # password unlocks them. Truly locked files still fail below.
        try:
            if reader.decrypt("") == 0:
                raise PDFReadError("This PDF is password-protected. Please unlock it and upload again.")
        except PDFReadError:
            raise
        except Exception as e:
            raise PDFReadError(f"This PDF is encrypted and could not be opened: {e}") from e

    pages = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            raw = page.extract_text() or ""
        except Exception as e:
            print(f"⚠️ Skipping page {i}: {e}")
            continue

        text = _clean_text(raw)
        if text:
            pages.append({"page": i, "text": text})

    if not pages:
        raise PDFReadError(
            "No text found in this PDF. It is probably a scanned/image-only PDF, "
            "which needs OCR. Please upload a text-based PDF."
        )

    print(f"📄 Read {len(pages)}/{len(reader.pages)} pages from {path.name}")
    return pages


def read_pdf_text(pdf_path: str, with_page_markers: bool = False) -> str:
    """
    Return the whole PDF as one string.
    with_page_markers=True prefixes each page with "[Page N]" so answers can
    cite where something came from.
    """
    pages = read_pdf_pages(pdf_path)
    if with_page_markers:
        return "\n\n".join(f"[Page {p['page']}]\n{p['text']}" for p in pages)
    return "\n\n".join(p["text"] for p in pages)


def pdf_to_transcript_file(pdf_path: str, with_page_markers: bool = True,
                           output_name: str | None = None) -> str:
    """
    Save the PDF's text to transcripts/<pdf name>.txt and return that path,
    so it can go straight into core.chunker.chunk_from_file() unchanged.
    output_name: name to use instead of the file's own (handy for Streamlit
    uploads, which are saved under random temp names).
    """
    text = read_pdf_text(pdf_path, with_page_markers=with_page_markers)

    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
    base = Path(output_name or pdf_path).stem
    base = re.sub(r"[^\w\-]+", "_", base).strip("_") or "document"
    output_path = os.path.join(TRANSCRIPT_DIR, f"{base}.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"💾 PDF text saved: {output_path} ({len(text)} characters)")
    return output_path
