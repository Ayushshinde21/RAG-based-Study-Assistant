from __future__ import annotations

import os
import uuid

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
except ImportError:
    pass


def main() -> int:
    os.environ["DATABASE_BACKEND"] = "postgres"
    os.environ["VECTOR_STORE_BACKEND"] = "postgres"

    has_url = bool(os.getenv("DATABASE_URL", "").strip())
    has_fields = all(os.getenv(key, "").strip() for key in ("DB_USER", "DB_PASSWORD", "DB_NAME"))
    if not (has_url or has_fields):
        raise SystemExit(
            "Configure DATABASE_URL or DB_USER, DB_PASSWORD, and DB_NAME before running this check."
        )

    try:
        import auth_store
        from langchain_core.documents import Document
        from core.vector_store import PostgresVectorStore, initialize_vector_store
        from storage.database import database_health, postgres_connection
    except ImportError as exc:
        raise SystemExit(f"A project dependency is missing: {exc}") from exc

    initialize_vector_store()
    health = database_health()
    if health.get("backend") != "postgres" or health.get("status") != "connected":
        raise RuntimeError(f"PostgreSQL health check failed: {health}")

    suffix = uuid.uuid4().hex
    email_a = f"pg-backend-check-a-{suffix}@example.invalid"
    email_b = f"pg-backend-check-b-{suffix}@example.invalid"
    password_a = f"A-{uuid.uuid4()}-Strong!"
    password_b = f"B-{uuid.uuid4()}-Strong!"
    user_a = None
    user_b = None
    store_a = None
    store_b = None
    collection = f"backend-check-{suffix[:12]}"

    try:
        user_a = auth_store.create_user(email_a, "PG Backend Check A", password_a, "student")
        user_b = auth_store.create_user(email_b, "PG Backend Check B", password_b, "student")

        authenticated = auth_store.authenticate_user(email_a, password_a)
        if not authenticated or authenticated["id"] != user_a["id"]:
            raise AssertionError("PostgreSQL account authentication failed.")

        session_token, _ = auth_store.create_session(user_a["id"])
        session = auth_store.get_session(session_token)
        if not session or session["user"]["id"] != user_a["id"]:
            raise AssertionError("PostgreSQL session persistence failed.")

        farm_a = auth_store.create_farm(user_a["id"], {"name": "PG verification farm A"})
        farm_b = auth_store.create_farm(user_b["id"], {"name": "PG verification farm B"})
        farm_ids_a = {farm["id"] for farm in auth_store.list_farms(user_a["id"])}
        farm_ids_b = {farm["id"] for farm in auth_store.list_farms(user_b["id"])}
        if farm_a["id"] not in farm_ids_a or farm_b["id"] not in farm_ids_b:
            raise AssertionError("PostgreSQL farm persistence failed.")
        if farm_b["id"] in farm_ids_a or farm_a["id"] in farm_ids_b:
            raise AssertionError("PostgreSQL farm owner isolation failed.")

        if not auth_store.set_user_active(user_a["id"], False):
            raise AssertionError("Could not disable the temporary verification account.")
        if auth_store.get_session(session_token) is not None:
            raise AssertionError("Disabling an account did not revoke its session.")

        store_a = PostgresVectorStore(collection, user_a["id"])
        store_b = PostgresVectorStore(collection, user_b["id"])
        store_a.add_documents([
            Document(
                page_content="Tenant A verification record: semantic and keyword retrieval must stay private.",
                metadata={"source": "backend-check-a.txt", "chunk_number": 1},
            )
        ])
        store_b.add_documents([
            Document(
                page_content="Tenant B verification record: separate owner data must not appear for tenant A.",
                metadata={"source": "backend-check-b.txt", "chunk_number": 1},
            )
        ])

        a_docs = store_a.get(include=["documents", "metadatas"])
        b_docs = store_b.get(include=["documents", "metadatas"])
        a_results = store_a.similarity_search("private semantic and keyword retrieval", k=3)
        b_results = store_b.similarity_search("separate owner data", k=3)

        if len(a_docs.get("documents", [])) != 1 or len(b_docs.get("documents", [])) != 1:
            raise AssertionError("Vector document retrieval did not preserve the two tenant scopes.")
        if not a_results or "tenant a" not in a_results[0].page_content.lower():
            raise AssertionError("Tenant A similarity search returned an unexpected result.")
        if not b_results or "tenant b" not in b_results[0].page_content.lower():
            raise AssertionError("Tenant B similarity search returned an unexpected result.")
        if any("tenant b" in doc.lower() for doc in a_docs["documents"]):
            raise AssertionError("Tenant A can read Tenant B documents.")
        if any("tenant a" in doc.lower() for doc in b_docs["documents"]):
            raise AssertionError("Tenant B can read Tenant A documents.")
        if a_docs["metadatas"][0].get("source") != "backend-check-a.txt":
            raise AssertionError("Document metadata was not preserved.")

        print("PostgreSQL connection: connected")
        print("Account authentication and session persistence: passed")
        print("Farm persistence and owner isolation: passed")
        print("Session revocation on account disable: passed")
        print("Vector writes, similarity search, and metadata reload: passed")
        print("Vector owner isolation: passed")
        print("SUCCESS: PostgreSQL + pgvector backend verification passed.")
        return 0
    finally:
        try:
            if store_a is not None:
                store_a.delete_collection()
        finally:
            try:
                if store_b is not None:
                    store_b.delete_collection()
            finally:
                temporary_user_ids = [
                    user["id"] for user in (user_a, user_b) if user is not None
                ]
                if temporary_user_ids:
                    with postgres_connection() as conn:
                        conn.execute(
                            "DELETE FROM users WHERE id = ANY(%s)",
                            (temporary_user_ids,),
                        )


if __name__ == "__main__":
    raise SystemExit(main())
