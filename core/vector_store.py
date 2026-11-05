from __future__ import annotations

import json
import os
import shutil
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from storage.database import postgres_connection, postgres_enabled

CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")
LECTURES_REGISTRY_PATH = os.path.join(CHROMA_DIR, "lectures.json")
VECTOR_STORE_BACKEND = os.getenv("VECTOR_STORE_BACKEND", "chroma").strip().lower()
VECTOR_DIMENSIONS = int(os.getenv("VECTOR_DIMENSIONS", "384"))
CHROMA_MODE = os.getenv("CHROMA_MODE", "local").strip().lower()
CHROMA_HOST = os.getenv("CHROMA_HOST", "127.0.0.1").strip()
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_SSL = os.getenv("CHROMA_SSL", "0").strip().lower() in {"1", "true", "yes"}
DEFAULT_COLLECTION = "lecture_chunks"
_embeddings_instance = None
_pg_schema_initialized = False
_pg_schema_lock = threading.Lock()

if VECTOR_STORE_BACKEND not in {"chroma", "postgres"}:
    raise ValueError("VECTOR_STORE_BACKEND must be either 'chroma' or 'postgres'.")
if VECTOR_STORE_BACKEND == "postgres" and not postgres_enabled():
    raise RuntimeError("Set DATABASE_BACKEND=postgres and DATABASE_URL when VECTOR_STORE_BACKEND=postgres.")
if not 1 <= VECTOR_DIMENSIONS <= 2000:
    raise ValueError("VECTOR_DIMENSIONS must be between 1 and 2000 for the configured HNSW index.")
if CHROMA_MODE not in {"local", "remote"}:
    raise ValueError("CHROMA_MODE must be either 'local' or 'remote'.")
if CHROMA_MODE == "remote" and not CHROMA_HOST:
    raise ValueError("CHROMA_HOST is required in remote mode.")


def get_embeddings():
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            model_kwargs={"device": os.getenv("EMBEDDING_DEVICE", "cpu")},
        )
    return _embeddings_instance


def _chroma_client_kwargs() -> dict:
    if CHROMA_MODE == "remote":
        kwargs = {"host": CHROMA_HOST, "port": CHROMA_PORT, "ssl": CHROMA_SSL}
        token = os.getenv("CHROMA_AUTH_TOKEN", "").strip()
        auth_header = os.getenv("CHROMA_AUTH_HEADER", "Authorization").strip().lower()
        require_auth = os.getenv("CHROMA_REQUIRE_AUTH", "0").strip().lower() in {"1", "true", "yes"}
        if auth_header not in {"authorization", "x-chroma-token"}:
            raise ValueError("CHROMA_AUTH_HEADER must be Authorization or X-Chroma-Token.")
        if require_auth and not token:
            raise RuntimeError("CHROMA_AUTH_TOKEN is required when CHROMA_REQUIRE_AUTH is enabled.")
        if token:
            header_name = "Authorization" if auth_header == "authorization" else "X-Chroma-Token"
            kwargs["headers"] = {
                header_name: f"Bearer {token}" if auth_header == "authorization" else token
            }
        return kwargs
    return {"persist_directory": CHROMA_DIR}


def _pgvector_types():
    try:
        from pgvector import Vector
        from pgvector.psycopg import register_vector
    except ImportError as exc:
        raise RuntimeError("Install pgvector and psycopg[binary] for PostgreSQL vector storage.") from exc
    return Vector, register_vector


def initialize_vector_store() -> None:
    global _pg_schema_initialized
    if VECTOR_STORE_BACKEND != "postgres" or _pg_schema_initialized:
        return
    with _pg_schema_lock:
        if _pg_schema_initialized:
            return
        with postgres_connection() as conn:
            extension = conn.execute(
                "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
            ).fetchone()
            if not extension:
                raise RuntimeError(
                    "PostgreSQL extension 'vector' is not enabled. "
                    "Ask the database administrator to run: CREATE EXTENSION IF NOT EXISTS vector;"
                )
            try:
                extension_version = tuple(
                    int(part) for part in str(extension["extversion"]).split(".")[:3]
                )
            except (TypeError, ValueError) as exc:
                raise RuntimeError(
                    "Could not determine the installed pgvector version."
                ) from exc
            if extension_version < (0, 5, 0):
                raise RuntimeError(
                    "pgvector 0.5.0 or newer is required because this backend creates an HNSW index. "
                    f"Detected version {extension['extversion']}."
                )
            conn.execute(
                f"""CREATE TABLE IF NOT EXISTS study_chunks (
                    id TEXT PRIMARY KEY,
                    collection_name TEXT NOT NULL,
                    owner_user_id BIGINT,
                    page_content TEXT NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                    embedding vector({VECTOR_DIMENSIONS}) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )"""
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_study_chunks_collection_owner "
                "ON study_chunks(collection_name, owner_user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_study_chunks_embedding "
                "ON study_chunks USING hnsw (embedding vector_cosine_ops)"
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS study_lectures (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    collection_name TEXT NOT NULL UNIQUE,
                    num_chunks INTEGER NOT NULL DEFAULT 0,
                    transcript_path TEXT,
                    owner_user_id BIGINT,
                    content_type TEXT NOT NULL DEFAULT 'lecture',
                    source_files JSONB NOT NULL DEFAULT '[]'::jsonb,
                    created_at TEXT NOT NULL
                )"""
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_study_lectures_owner_created "
                "ON study_lectures(owner_user_id, created_at DESC)"
            )
        _pg_schema_initialized = True


@contextmanager
def _pg_connection() -> Iterator[object]:
    Vector, register_vector = _pgvector_types()
    with postgres_connection() as conn:
        register_vector(conn)
        yield conn


class _PostgresDenseRetriever:
    def __init__(self, store: "PostgresVectorStore", k: int):
        self.store = store
        self.k = max(1, int(k))

    def invoke(self, query: str, config=None, **kwargs) -> list[Document]:
        return self.store.similarity_search(query, k=self.k)

    def get_relevant_documents(self, query: str) -> list[Document]:
        return self.invoke(query)


class PostgresVectorStore:
    def __init__(self, collection_name: str, owner_user_id: int | None = None):
        if not collection_name or len(collection_name) > 128:
            raise ValueError("Invalid vector collection name.")
        initialize_vector_store()
        self.collection_name = collection_name
        self.owner_user_id = int(owner_user_id) if owner_user_id is not None else None

    def _insert_documents(self, conn, documents: list[Document], vectors: list[list[float]]) -> list[str]:
        if not documents:
            return []
        Vector, _ = _pgvector_types()
        try:
            from psycopg.types.json import Jsonb
        except ImportError as exc:
            raise RuntimeError("Install psycopg[binary] for PostgreSQL vector storage.") from exc
        ids = [uuid.uuid4().hex for _ in documents]
        conn.executemany(
            """INSERT INTO study_chunks
               (id, collection_name, owner_user_id, page_content, metadata, embedding)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            [
                (
                    doc_id,
                    self.collection_name,
                    self.owner_user_id,
                    doc.page_content,
                    Jsonb(dict(doc.metadata or {})),
                    Vector(vector),
                )
                for doc_id, doc, vector in zip(ids, documents, vectors)
            ],
        )
        return ids

    def _embed_documents(self, documents: list[Document]) -> list[list[float]]:
        vectors = get_embeddings().embed_documents([doc.page_content for doc in documents])
        if len(vectors) != len(documents) or any(len(vector) != VECTOR_DIMENSIONS for vector in vectors):
            raise RuntimeError(
                f"Embedding dimensions do not match VECTOR_DIMENSIONS={VECTOR_DIMENSIONS}."
            )
        return vectors

    def add_documents(self, documents: list[Document]) -> list[str]:
        if not documents:
            return []
        vectors = self._embed_documents(documents)
        with _pg_connection() as conn:
            return self._insert_documents(conn, documents, vectors)

    def replace_documents(self, documents: list[Document]) -> list[str]:
        vectors = self._embed_documents(documents) if documents else []
        with _pg_connection() as conn:
            conn.execute(
                """DELETE FROM study_chunks
                   WHERE collection_name = %s
                     AND owner_user_id IS NOT DISTINCT FROM %s""",
                (self.collection_name, self.owner_user_id),
            )
            return self._insert_documents(conn, documents, vectors)

    def similarity_search(self, query: str, k: int = 10) -> list[Document]:
        if not query.strip():
            return []
        result_limit = max(1, min(int(k), 100))
        vector = get_embeddings().embed_query(query)
        if len(vector) != VECTOR_DIMENSIONS:
            raise RuntimeError(
                f"Embedding dimensions do not match VECTOR_DIMENSIONS={VECTOR_DIMENSIONS}."
            )
        Vector, _ = _pgvector_types()
        with _pg_connection() as conn:
            extension = conn.execute(
                "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
            ).fetchone()
            extension_version = str(extension["extversion"]) if extension else "0.0.0"
            version_parts = tuple(
                int(part) for part in extension_version.split(".")[:3]
                if part.isdigit()
            )
            if version_parts >= (0, 5, 0):
                conn.execute(
                    "SELECT set_config('hnsw.ef_search', %s, true)",
                    (str(max(40, min(200, result_limit * 10))),),
                )
            if version_parts >= (0, 8, 0):
                conn.execute(
                    "SELECT set_config('hnsw.iterative_scan', 'strict_order', true)"
                )
            rows = conn.execute(
                """SELECT page_content, metadata
                   FROM study_chunks
                   WHERE collection_name = %s
                     AND owner_user_id IS NOT DISTINCT FROM %s
                   ORDER BY embedding <=> %s
                   LIMIT %s""",
                (self.collection_name, self.owner_user_id, Vector(vector), result_limit),
            ).fetchall()
        return [Document(page_content=row["page_content"], metadata=dict(row["metadata"] or {})) for row in rows]

    def get(self, include: list[str] | None = None) -> dict:
        with _pg_connection() as conn:
            rows = conn.execute(
                """SELECT id, page_content, metadata
                   FROM study_chunks
                   WHERE collection_name = %s
                     AND owner_user_id IS NOT DISTINCT FROM %s
                   ORDER BY created_at, id""",
                (self.collection_name, self.owner_user_id),
            ).fetchall()
        result = {"ids": [row["id"] for row in rows]}
        if include is None or "documents" in include:
            result["documents"] = [row["page_content"] for row in rows]
        if include is None or "metadatas" in include:
            result["metadatas"] = [dict(row["metadata"] or {}) for row in rows]
        return result

    def count(self) -> int:
        with _pg_connection() as conn:
            row = conn.execute(
                """SELECT COUNT(*) AS total FROM study_chunks
                   WHERE collection_name = %s
                     AND owner_user_id IS NOT DISTINCT FROM %s""",
                (self.collection_name, self.owner_user_id),
            ).fetchone()
        return int(row["total"])

    def delete_collection(self, include_all_owners: bool = False) -> None:
        with _pg_connection() as conn:
            if include_all_owners:
                conn.execute(
                    "DELETE FROM study_chunks WHERE collection_name = %s",
                    (self.collection_name,),
                )
            else:
                conn.execute(
                    "DELETE FROM study_chunks WHERE collection_name = %s AND owner_user_id IS NOT DISTINCT FROM %s",
                    (self.collection_name, self.owner_user_id),
                )

    def as_retriever(self, search_type: str = "similarity", search_kwargs: dict | None = None):
        if search_type != "similarity":
            raise ValueError("PostgreSQL vector store supports similarity retrieval only.")
        return _PostgresDenseRetriever(self, (search_kwargs or {}).get("k", 10))


def clear_vector_store() -> None:
    if VECTOR_STORE_BACKEND == "postgres":
        raise RuntimeError("Full PostgreSQL vector-store clearing is disabled. Delete individual lectures instead.")
    if CHROMA_MODE == "remote":
        raise RuntimeError("Full vector-store clearing is disabled in remote mode. Delete individual lecture collections instead.")
    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
        print("Local ChromaDB directory cleared.")


def delete_collection(collection_name: str, owner_user_id: int | None = None) -> None:
    if VECTOR_STORE_BACKEND == "postgres":
        PostgresVectorStore(collection_name, owner_user_id).delete_collection()
        return
    if CHROMA_MODE == "local" and not os.path.exists(CHROMA_DIR):
        return
    try:
        from langchain_chroma import Chroma
        store = Chroma(
            collection_name=collection_name,
            embedding_function=get_embeddings(),
            **_chroma_client_kwargs(),
        )
        store.delete_collection()
        print(f"Deleted collection: {collection_name}")
    except Exception as exc:
        print(f"Could not delete collection {collection_name}: {exc}")


def build_vector_store(
    docs: list[Document],
    reset: bool = True,
    collection_name: str = DEFAULT_COLLECTION,
    owner_user_id: int | None = None,
):
    print(f"Building {VECTOR_STORE_BACKEND} vector store (collection: {collection_name})...")
    if reset:
        delete_collection(collection_name, owner_user_id=owner_user_id)
    if VECTOR_STORE_BACKEND == "postgres":
        initialize_vector_store()
        vector_store = PostgresVectorStore(collection_name, owner_user_id)
        vector_store.add_documents(docs)
    else:
        from langchain_chroma import Chroma
        embeddings = get_embeddings()
        if CHROMA_MODE == "remote":
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                **_chroma_client_kwargs(),
            )
            if docs:
                vector_store.add_documents(docs)
        else:
            vector_store = Chroma.from_documents(
                documents=docs,
                embedding=embeddings,
                persist_directory=CHROMA_DIR,
                collection_name=collection_name,
            )
    print(f"Vector store built. {len(docs)} chunks indexed.")
    return vector_store


def load_vector_store(collection_name: str = DEFAULT_COLLECTION, owner_user_id: int | None = None):
    if VECTOR_STORE_BACKEND == "postgres":
        initialize_vector_store()
        return PostgresVectorStore(collection_name, owner_user_id)
    if CHROMA_MODE == "local" and not os.path.exists(CHROMA_DIR):
        raise FileNotFoundError("No vector store found. Run build first.")
    from langchain_chroma import Chroma
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        **_chroma_client_kwargs(),
    )


def get_all_docs_from_store(vector_store) -> list[Document]:
    raw = vector_store.get(include=["documents", "metadatas"])
    return [
        Document(page_content=text, metadata=meta or {})
        for text, meta in zip(raw.get("documents", []), raw.get("metadatas", []))
    ]


def _load_registry() -> list[dict]:
    if not os.path.exists(LECTURES_REGISTRY_PATH):
        return []
    try:
        with open(LECTURES_REGISTRY_PATH, "r", encoding="utf-8") as file:
            content = json.load(file)
        return content if isinstance(content, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_registry(lectures: list[dict]) -> None:
    os.makedirs(CHROMA_DIR, exist_ok=True)
    temporary_path = LECTURES_REGISTRY_PATH + ".tmp"
    with open(temporary_path, "w", encoding="utf-8") as file:
        json.dump(lectures, file, indent=2, ensure_ascii=False)
    os.replace(temporary_path, LECTURES_REGISTRY_PATH)


def register_lecture(
    title: str,
    collection_name: str,
    num_chunks: int,
    transcript_path: str | None = None,
    owner_user_id: int | None = None,
    content_type: str = "lecture",
    source_files: list[str] | None = None,
    created_at: str | None = None,
) -> str:
    lecture_id = collection_name
    created_at = created_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    stored_transcript = transcript_path
    if VECTOR_STORE_BACKEND == "postgres" and stored_transcript and not stored_transcript.startswith("gs://"):
        stored_transcript = None
    record = {
        "id": lecture_id,
        "title": title,
        "collection_name": collection_name,
        "num_chunks": int(num_chunks),
        "transcript_path": stored_transcript,
        "owner_user_id": owner_user_id,
        "content_type": content_type,
        "source_files": list(source_files or []),
        "created_at": created_at,
    }
    if VECTOR_STORE_BACKEND == "postgres":
        initialize_vector_store()
        try:
            from psycopg.types.json import Jsonb
        except ImportError as exc:
            raise RuntimeError("Install psycopg[binary] for PostgreSQL storage.") from exc
        with postgres_connection() as conn:
            conn.execute(
                """INSERT INTO study_lectures
                   (id, title, collection_name, num_chunks, transcript_path, owner_user_id,
                    content_type, source_files, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO UPDATE SET
                     title = EXCLUDED.title,
                     num_chunks = EXCLUDED.num_chunks,
                     transcript_path = EXCLUDED.transcript_path,
                     owner_user_id = EXCLUDED.owner_user_id,
                     content_type = EXCLUDED.content_type,
                     source_files = EXCLUDED.source_files""",
                (
                    lecture_id, title, collection_name, int(num_chunks), stored_transcript,
                    owner_user_id, content_type, Jsonb(list(source_files or [])), created_at,
                ),
            )
    else:
        lectures = [item for item in _load_registry() if item.get("id") != lecture_id]
        lectures.append(record)
        _save_registry(lectures)
    return lecture_id


def list_lectures() -> list[dict]:
    if VECTOR_STORE_BACKEND == "postgres":
        initialize_vector_store()
        with postgres_connection() as conn:
            rows = conn.execute(
                "SELECT id, title, collection_name, num_chunks, transcript_path, owner_user_id, content_type, source_files, created_at FROM study_lectures ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]
    return sorted(_load_registry(), key=lambda item: item.get("created_at", ""), reverse=True)


def get_lecture(lecture_id: str) -> dict | None:
    if VECTOR_STORE_BACKEND == "postgres":
        initialize_vector_store()
        with postgres_connection() as conn:
            row = conn.execute(
                "SELECT id, title, collection_name, num_chunks, transcript_path, owner_user_id, content_type, source_files, created_at FROM study_lectures WHERE id = %s",
                (lecture_id,),
            ).fetchone()
        return dict(row) if row else None
    return next((item for item in _load_registry() if item.get("id") == lecture_id), None)


def rename_lecture(lecture_id: str, title: str) -> bool:
    if VECTOR_STORE_BACKEND == "postgres":
        initialize_vector_store()
        with postgres_connection() as conn:
            cursor = conn.execute("UPDATE study_lectures SET title = %s WHERE id = %s", (title, lecture_id))
            return cursor.rowcount > 0
    lectures = _load_registry()
    found = False
    for lecture in lectures:
        if lecture.get("id") == lecture_id:
            lecture["title"] = title
            found = True
            break
    if found:
        _save_registry(lectures)
    return found


def new_collection_name() -> str:
    return f"lecture_{uuid.uuid4().hex[:10]}"


def delete_lecture(lecture_id: str) -> None:
    lecture = get_lecture(lecture_id)
    if lecture:
        delete_collection(
            lecture["collection_name"],
            owner_user_id=lecture.get("owner_user_id"),
        )
    if VECTOR_STORE_BACKEND == "postgres":
        with postgres_connection() as conn:
            conn.execute("DELETE FROM study_lectures WHERE id = %s", (lecture_id,))
        return
    _save_registry([item for item in _load_registry() if item.get("id") != lecture_id])


def get_dense_retriever(vector_store, k: int = 10):
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )
