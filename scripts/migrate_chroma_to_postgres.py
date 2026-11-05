from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
except ImportError:
    pass


def _collection_name(item) -> str:
    return str(getattr(item, "name", item))

def _read_registry(path: Path, titles_path: Path) -> dict[str, dict]:
    registry = {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            registry = {
                item.get("collection_name", item.get("id")): item
                for item in data
                if isinstance(item, dict) and item.get("collection_name", item.get("id"))
            }
    except (OSError, json.JSONDecodeError):
        pass
    try:
        titles = json.loads(titles_path.read_text(encoding="utf-8"))
        if isinstance(titles, dict):
            for collection_name, title in titles.items():
                if collection_name in registry and isinstance(title, str) and title.strip():
                    registry[collection_name]["title"] = title.strip()
    except (OSError, json.JSONDecodeError):
        pass
    return registry

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy every collection from a local Chroma directory into PostgreSQL + pgvector."
    )
    parser.add_argument("--chroma-dir", default=os.getenv("CHROMA_DIR", "chroma_db"))
    parser.add_argument("--registry", default=None)
    parser.add_argument("--titles", default="lecture_titles.json")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    chroma_dir = Path(args.chroma_dir).resolve()
    if not chroma_dir.is_dir():
        raise SystemExit(f"Chroma directory not found: {chroma_dir}")

    try:
        import chromadb
    except ImportError as exc:
        raise SystemExit(f"A project dependency is missing: {exc}") from exc

    registry_path = Path(args.registry) if args.registry else chroma_dir / "lectures.json"
    registry = _read_registry(registry_path, Path(args.titles))
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collections = client.list_collections()

    if args.dry_run:
        planned_collections = 0
        planned_documents = 0
        for collection_ref in collections:
            name = _collection_name(collection_ref)
            raw = client.get_collection(name).get(include=["documents", "metadatas"])
            docs = [
                text for text in (raw.get("documents") or [])
                if isinstance(text, str) and text.strip()
            ]
            entry = registry.get(name, {})
            print(f"PLAN {name}: {len(docs)} chunks, owner={entry.get('owner_user_id')}")
            planned_collections += 1
            planned_documents += len(docs)
        print(
            "DRY RUN COMPLETE: "
            f"collections={planned_collections}, chunks={planned_documents}. "
            "No PostgreSQL connection or destination writes were performed."
        )
        return 0

    has_url = bool(os.getenv("DATABASE_URL", "").strip())
    has_fields = all(os.getenv(key, "").strip() for key in ("DB_USER", "DB_PASSWORD", "DB_NAME"))
    if not (has_url or has_fields):
        raise SystemExit("Configure DATABASE_URL or DB_USER, DB_PASSWORD, and DB_NAME before running this migration.")

    os.environ["DATABASE_BACKEND"] = "postgres"
    os.environ["VECTOR_STORE_BACKEND"] = "postgres"

    try:
        from langchain_core.documents import Document
        from core.vector_store import PostgresVectorStore, initialize_vector_store, register_lecture
        from storage.database import postgres_connection
    except ImportError as exc:
        raise SystemExit(f"A project dependency is missing: {exc}") from exc

    initialize_vector_store()
    with postgres_connection() as conn:
        map_table = conn.execute(
            "SELECT to_regclass('public.migration_user_id_map') AS table_name"
        ).fetchone()
        if map_table and map_table["table_name"]:
            id_rows = conn.execute(
                "SELECT source_user_id,target_user_id FROM migration_user_id_map"
            ).fetchall()
        else:
            id_rows = []
    user_id_map = {
        int(row["source_user_id"]): int(row["target_user_id"])
        for row in id_rows
    }

    migrated = 0
    skipped = 0
    total_documents = 0
    for collection_ref in collections:
        name = _collection_name(collection_ref)
        raw = client.get_collection(name).get(include=["documents", "metadatas"])
        texts = raw.get("documents") or []
        metadatas = raw.get("metadatas") or []
        docs = [
            Document(page_content=text, metadata=metadata or {})
            for text, metadata in zip(texts, metadatas)
            if isinstance(text, str) and text.strip()
        ]
        entry = registry.get(name, {})
        source_owner_id = entry.get("owner_user_id")
        if source_owner_id is None:
            owner_user_id = None
        else:
            try:
                source_owner_id = int(source_owner_id)
            except (TypeError, ValueError) as exc:
                raise SystemExit(f"Collection {name} has an invalid owner_user_id in its lecture registry.") from exc
            if source_owner_id not in user_id_map:
                raise SystemExit(
                    f"Collection {name} belongs to source user {source_owner_id}, "
                    "but no migrated user-ID mapping exists. Run the SQLite account migration first."
                )
            owner_user_id = user_id_map[source_owner_id]

        store = PostgresVectorStore(name, owner_user_id)
        existing_count = store.count()

        if args.replace and existing_count and not docs:
            raise SystemExit(
                f"Refusing to replace {name}: the source collection contains no readable documents, "
                "but the destination has existing chunks. Inspect the source before retrying."
            )

        if existing_count and not args.replace:
            register_lecture(
                title=str(entry.get("title") or name),
                collection_name=name,
                num_chunks=existing_count,
                transcript_path=entry.get("transcript_path"),
                owner_user_id=owner_user_id,
                content_type=str(entry.get("content_type") or "lecture"),
                source_files=entry.get("source_files") or [],
                created_at=entry.get("created_at"),
            )
            skipped += 1
            print(f"SKIP {name}: {existing_count} destination chunks already exist")
            continue

        store.replace_documents(docs) if args.replace else store.add_documents(docs)
        if entry or docs:
            register_lecture(
                title=str(entry.get("title") or name),
                collection_name=name,
                num_chunks=len(docs),
                transcript_path=entry.get("transcript_path"),
                owner_user_id=owner_user_id,
                content_type=str(entry.get("content_type") or "lecture"),
                source_files=entry.get("source_files") or [],
                created_at=entry.get("created_at"),
            )
        migrated += 1
        total_documents += len(docs)
        print(f"MIGRATED {name}: {len(docs)} chunks")

    print(
        f"Migration complete. migrated_collections={migrated}, "
        f"skipped_collections={skipped}, migrated_chunks={total_documents}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
