from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator


def database_backend() -> str:
    configured = os.getenv("DATABASE_BACKEND", "auto").strip().lower()
    if configured == "auto":
        has_url = bool(os.getenv("DATABASE_URL", "").strip())
        has_fields = all(os.getenv(key, "").strip() for key in ("DB_USER", "DB_NAME", "DB_PASSWORD"))
        return "postgres" if has_url or has_fields else "sqlite"
    if configured not in {"sqlite", "postgres"}:
        raise RuntimeError("DATABASE_BACKEND must be auto, sqlite, or postgres.")
    return configured


def postgres_enabled() -> bool:
    return database_backend() == "postgres"


def connect_postgres():
    dsn = os.getenv("DATABASE_URL", "").strip()
    required = ("DB_USER", "DB_PASSWORD", "DB_NAME")
    missing = [key for key in required if not os.getenv(key, "").strip()]
    if not dsn and missing:
        raise RuntimeError("Set DATABASE_URL or configure PostgreSQL fields: " + ", ".join(missing))
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise RuntimeError("Install psycopg[binary] to use the PostgreSQL backend.") from exc
    timeout = max(1, int(os.getenv("DATABASE_CONNECT_TIMEOUT_SECONDS", "10")))
    if dsn:
        return psycopg.connect(dsn, row_factory=dict_row, connect_timeout=timeout)
    unix_socket = os.getenv("INSTANCE_UNIX_SOCKET", "").strip()
    host = unix_socket or os.getenv("DB_HOST", "127.0.0.1").strip()
    port = int(os.getenv("DB_PORT", "5432"))
    sslmode = os.getenv("DB_SSLMODE", "").strip() or ("disable" if unix_socket else "prefer")
    return psycopg.connect(
        host=host,
        port=port,
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        row_factory=dict_row,
        connect_timeout=timeout,
        sslmode=sslmode,
    )


@contextmanager
def postgres_connection() -> Iterator[object]:
    conn = connect_postgres()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def database_health() -> dict[str, str]:
    if not postgres_enabled():
        return {"backend": "sqlite", "status": "local"}
    with postgres_connection() as conn:
        conn.execute("SELECT 1").fetchone()
    return {"backend": "postgres", "status": "connected"}
