import os
import json
import shutil
import uuid
from datetime import datetime
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# persistent storage folder
CHROMA_DIR = "chroma_db"

# Default collection name — kept for back-compat with main.py / existing
# tests that call build_vector_store()/load_vector_store() with no
# collection_name. New lectures (via app.py) each get their own collection
# instead, so uploading a second lecture doesn't wipe or mix with the first.
DEFAULT_COLLECTION = "lecture_chunks"

# Small on-disk registry of every lecture that's been processed, so "My
# Lectures" can list and reopen past lectures instead of only knowing about
# whatever is in the current Streamlit session.
LECTURES_REGISTRY_PATH = os.path.join(CHROMA_DIR, "lectures.json")

# shared embeddings instance — loaded once, reused everywhere
_embeddings_instance = None


def get_embeddings():
    """
    Load HuggingFace embedding model.
    Reuses the same instance across calls instead of reloading each time.
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"}
        )
    return _embeddings_instance


def clear_vector_store():
    """
    Delete the existing ChromaDB folder completely — ALL lectures, not just
    one. Kept for back-compat / a full reset; prefer delete_collection() for
    removing a single lecture without touching the others.
    """
    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
        print("🗑️  Cleared previous vector store")


def delete_collection(collection_name: str):
    """Delete a single lecture's collection, leaving every other one intact."""
    if not os.path.exists(CHROMA_DIR):
        return
    try:
        Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=get_embeddings(),
            collection_name=collection_name,
        ).delete_collection()
        print(f"🗑️  Deleted collection: {collection_name}")
    except Exception as e:
        print(f"⚠️  Could not delete collection {collection_name}: {e}")


def build_vector_store(docs: list[Document], reset: bool = True,
                        collection_name: str = DEFAULT_COLLECTION) -> Chroma:
    """
    Build a ChromaDB vector store from documents, saved to disk so it
    persists between runs.

    Each lecture should get its own collection_name (see
    register_lecture/list_lectures below) so multiple processed lectures can
    coexist — reset=True then only clears THIS collection, not the whole
    chroma_db folder, so earlier lectures are left alone.
    """
    print(f"🔨 Building ChromaDB vector store (collection: {collection_name})...")

    if reset:
        delete_collection(collection_name)

    embeddings = get_embeddings()

    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=collection_name,
    )

    print(f"✅ Vector store built! {len(docs)} chunks indexed")
    return vector_store


def load_vector_store(collection_name: str = DEFAULT_COLLECTION) -> Chroma:
    """
    Load an existing lecture's collection from disk by name.
    """
    if not os.path.exists(CHROMA_DIR):
        raise FileNotFoundError("No vector store found. Run build first.")

    embeddings = get_embeddings()

    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=collection_name,
    )

    print(f"✅ Vector store loaded from disk (collection: {collection_name})")
    return vector_store


def get_all_docs_from_store(vector_store: Chroma) -> list[Document]:
    """
    Pull every chunk back out of a collection as Documents — used when
    reopening a past lecture from "My Lectures", since BM25's retriever is
    in-memory only and needs to be rebuilt from the same chunks the dense
    index already has.
    """
    raw = vector_store.get(include=["documents", "metadatas"])
    return [
        Document(page_content=text, metadata=meta or {})
        for text, meta in zip(raw.get("documents", []), raw.get("metadatas", []))
    ]


# ── Lecture registry ─────────────────────────────────────────────────────────
# A small JSON file tracking every lecture that's been processed, independent
# of any single Streamlit session, so "My Lectures" has something real to
# show and reopen instead of only ever knowing about the current upload.

def _load_registry() -> list[dict]:
    if not os.path.exists(LECTURES_REGISTRY_PATH):
        return []
    try:
        with open(LECTURES_REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_registry(lectures: list[dict]):
    os.makedirs(CHROMA_DIR, exist_ok=True)
    with open(LECTURES_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(lectures, f, indent=2)


def register_lecture(title: str, collection_name: str, num_chunks: int,
                      transcript_path: str | None = None) -> str:
    """Add a newly processed lecture to the registry. Returns its lecture_id."""
    lecture_id = collection_name  # collection_name is already unique per lecture
    lectures = _load_registry()
    lectures.append({
        "id": lecture_id,
        "title": title,
        "collection_name": collection_name,
        "num_chunks": num_chunks,
        "transcript_path": transcript_path,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })
    _save_registry(lectures)
    return lecture_id


def list_lectures() -> list[dict]:
    """All registered lectures, newest first."""
    return sorted(_load_registry(), key=lambda l: l.get("created_at", ""), reverse=True)


def get_lecture(lecture_id: str) -> dict | None:
    for lecture in _load_registry():
        if lecture["id"] == lecture_id:
            return lecture
    return None


def new_collection_name() -> str:
    """A short, unique collection name for a newly uploaded lecture."""
    return f"lecture_{uuid.uuid4().hex[:10]}"


def delete_lecture(lecture_id: str):
    """Remove a lecture's vector collection and its registry entry."""
    lecture = get_lecture(lecture_id)
    if lecture:
        delete_collection(lecture["collection_name"])
    lectures = [l for l in _load_registry() if l["id"] != lecture_id]
    _save_registry(lectures)


def get_dense_retriever(vector_store: Chroma, k: int = 10):
    """
    Get dense retriever from vector store.
    Returns top-k most similar chunks.
    """
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )
