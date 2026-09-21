import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.documents import Document
from core.vector_store import get_embeddings   # ← use shared instance


def load_transcript(transcript_path: str) -> str:
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"Transcript not found: {transcript_path}")

    with open(transcript_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    print(f"📄 Loaded transcript: {len(text)} characters")
    return text


def chunk_fixed(text: str, source: str = "unknown",
                chunk_size: int = 500, overlap: int = 50) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", "!", "?", " "]
    )
    chunks = splitter.split_text(text)
    chunks = [c.strip() for c in chunks if c.strip()]

    docs = [
        Document(
            page_content=chunk,
            metadata={"source": source, "chunk_id": i, "method": "fixed"}
        )
        for i, chunk in enumerate(chunks)
    ]

    print(f"✂️  Fixed chunking: {len(docs)} chunks")
    return docs


def chunk_semantic(text: str, source: str = "unknown") -> list[Document]:
    embeddings = get_embeddings()   # ← shared, not reloaded

    splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="standard_deviation",
        breakpoint_threshold_amount=1.0
    )

    chunks = splitter.split_text(text)
    chunks = [c.strip() for c in chunks if c.strip()]

    docs = [
        Document(
            page_content=chunk,
            metadata={"source": source, "chunk_id": i, "method": "semantic"}
        )
        for i, chunk in enumerate(chunks)
    ]

    print(f"✂️  Semantic chunking: {len(docs)} chunks")
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
        print("⚠️  Short text detected — switching to fixed chunking")
        method = "fixed"

    docs = chunk_text(text, source=source, method=method)

    print(f"\n📦 Sample chunk (chunk 1 of {len(docs)}):")
    print("-" * 50)
    print(docs[0].page_content[:300] if docs else "No chunks generated")
    print("-" * 50)
    print(f"Metadata: {docs[0].metadata if docs else {}}")

    return docs
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


def load_transcript(transcript_path: str) -> str:
    """
    Load transcript text from a .txt file.
    """
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"Transcript not found: {transcript_path}")

    with open(transcript_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    print(f"📄 Loaded transcript: {len(text)} characters")
    return text


def chunk_fixed(text: str, source: str = "unknown",
                chunk_size: int = 500, overlap: int = 50) -> list[Document]:
    """
    Fixed-size chunking — baseline for comparison.
    Returns list of Document objects.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", "!", "?", " "]
    )
    chunks = splitter.split_text(text)

    # filter empty chunks
    chunks = [c.strip() for c in chunks if c.strip()]

    # wrap in Document objects with metadata
    docs = [
        Document(
            page_content=chunk,
            metadata={"source": source, "chunk_id": i, "method": "fixed"}
        )
        for i, chunk in enumerate(chunks)
    ]

    print(f"✂️  Fixed chunking: {len(docs)} chunks")
    return docs


def chunk_semantic(text: str, source: str = "unknown") -> list[Document]:
    """
    Semantic chunking — splits at topic boundaries.
    Returns list of Document objects.
    """
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )

    splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="standard_deviation",
        breakpoint_threshold_amount=1.0   # lower = more chunks
    )

    chunks = splitter.split_text(text)

    # filter empty chunks
    chunks = [c.strip() for c in chunks if c.strip()]

    # wrap in Document objects with metadata
    docs = [
        Document(
            page_content=chunk,
            metadata={"source": source, "chunk_id": i, "method": "semantic"}
        )
        for i, chunk in enumerate(chunks)
    ]

    print(f"✂️  Semantic chunking: {len(docs)} chunks")
    return docs


def chunk_text(text: str, source: str = "unknown",
               method: str = "semantic") -> list[Document]:
    """
    Main entry point.
    method: "semantic" (default) or "fixed"
    Returns list of Document objects.
    """
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

    # use fixed chunking for short texts (under 2000 chars)
    if len(text) < 2000:
        print("⚠️  Short text detected — switching to fixed chunking")
        method = "fixed"

    docs = chunk_text(text, source=source, method=method)

    print(f"\n📦 Sample chunk (chunk 1 of {len(docs)}):")
    print("-" * 50)
    print(docs[0].page_content[:300] if docs else "No chunks generated")
    print("-" * 50)
    print(f"Metadata: {docs[0].metadata if docs else {}}")

    return docs 