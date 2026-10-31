import os
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# NOTE: SemanticChunker and get_embeddings are imported lazily inside
# chunk_semantic(), so short transcripts (fixed chunking) never load
# langchain_experimental / the embedding stack.

_SOURCE_MARKER_PATTERN = re.compile(
    r"(?m)^[ \t]*\[(Page|Slide)\s+(\d+)\][ \t]*(?:\r?\n|$)"
)
_TIMESTAMP_PATTERN = re.compile(
    r"\[(?:(\d{1,3}):)?([0-5]?\d):([0-5]\d)\]"
)


def load_transcript(transcript_path: str) -> str:
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"Transcript not found: {transcript_path}")

    with open(transcript_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    print(f"📄 Loaded transcript: {len(text)} characters", flush=True)
    return text


def _split_marked_sections(text: str) -> list[tuple[str | None, int | None, str]] | None:
    """Split text carrying [Page N] or [Slide N] markers into located sections."""
    matches = list(_SOURCE_MARKER_PATTERN.finditer(text))
    if not matches:
        return None

    sections: list[tuple[str | None, int | None, str]] = []
    prefix = text[:matches[0].start()].strip()
    if prefix:
        sections.append((None, None, prefix))

    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[match.end():end].strip()
        if content:
            sections.append((match.group(1).lower(), int(match.group(2)), content))

    return sections


def _extract_start_time(text: str) -> str | None:
    """Return the first timestamp marker from a timestamped transcript chunk."""
    match = _TIMESTAMP_PATTERN.search(text or "")
    if not match:
        return None
    return match.group(0)[1:-1]


def _base_metadata(source: str, chunk_id: int, method: str) -> dict:
    metadata = {
        "source": source,
        "chunk_id": chunk_id,
        "document_chunk": chunk_id,
        "method": method,
    }
    if source and source != "unknown":
        metadata["filename"] = source
    return metadata


def chunk_fixed(text: str, source: str = "unknown",
                chunk_size: int = 500, overlap: int = 50) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", "!", "?", " "],
    )

    marked_sections = _split_marked_sections(text)
    sections = marked_sections if marked_sections is not None else [(None, None, text)]

    docs: list[Document] = []
    for location_type, location_number, section_text in sections:
        chunks = splitter.split_text(section_text)
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            metadata = _base_metadata(source, len(docs), "fixed")
            if location_type == "page":
                metadata["page_number"] = location_number
            elif location_type == "slide":
                metadata["slide_number"] = location_number

            start_time = _extract_start_time(chunk)
            if start_time:
                metadata["start_time_str"] = start_time

            docs.append(Document(page_content=chunk, metadata=metadata))

    print(f"✂️  Fixed chunking: {len(docs)} chunks", flush=True)
    return docs


def chunk_semantic(text: str, source: str = "unknown") -> list[Document]:
    from langchain_experimental.text_splitter import SemanticChunker  # lazy
    from core.vector_store import get_embeddings                      # lazy

    embeddings = get_embeddings()   # shared, not reloaded

    splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="standard_deviation",
        breakpoint_threshold_amount=1.0,
    )

    chunks = splitter.split_text(text)
    chunks = [c.strip() for c in chunks if c.strip()]

    docs = []
    for index, chunk in enumerate(chunks):
        metadata = _base_metadata(source, index, "semantic")
        start_time = _extract_start_time(chunk)
        if start_time:
            metadata["start_time_str"] = start_time
        docs.append(Document(page_content=chunk, metadata=metadata))

    print(f"✂️  Semantic chunking: {len(docs)} chunks", flush=True)
    return docs


def chunk_text(text: str, source: str = "unknown",
               method: str = "semantic") -> list[Document]:
    if not text.strip():
        raise ValueError("Empty text — nothing to chunk")

    if method == "semantic":
        return chunk_semantic(text, source)
    elif method == "fixed":
        return chunk_fixed(text, source)
    else:
        raise ValueError(f"Unknown method: {method}. Use 'semantic' or 'fixed'")


def chunk_from_file(transcript_path: str,
                    method: str = "semantic") -> list[Document]:
    text = load_transcript(transcript_path)
    source = os.path.basename(transcript_path)

    if len(text) < 2000:
        print("⚠️  Short text detected — switching to fixed chunking", flush=True)
        method = "fixed"

    docs = chunk_text(text, source=source, method=method)

    print(f"\n📦 Sample chunk (chunk 1 of {len(docs)}):")
    print("-" * 50)
    print(docs[0].page_content[:300] if docs else "No chunks generated")
    print("-" * 50)
    print(f"Metadata: {docs[0].metadata if docs else {}}", flush=True)

    return docs
