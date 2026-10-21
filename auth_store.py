"""Small SQLite-backed account, session, and farm store for local deployments.

For multi-instance production deployments, replace SQLite with a managed database
and move lecture/vector files to shared durable storage.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

PASSWORD_ITERATIONS = 310_000
SESSION_TTL_SECONDS = 60 * 60 * 24 * 7
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _db_path() -> str:
    return os.getenv("AUTH_DB_PATH", "auth.sqlite3")


def _connect() -> sqlite3.Connection:
    path = _db_path()
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def _connection():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_auth_db() -> None:
    with _connection() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('student','farmer','admin')),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                csrf_token TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
            CREATE TABLE IF NOT EXISTS farms (
                id TEXT PRIMARY KEY,
                owner_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT '',
                crop TEXT NOT NULL DEFAULT '',
                soil_moisture REAL,
                temperature_c REAL,
                humidity_pct REAL,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_farms_owner ON farms(owner_user_id);
            """
        )
        email = os.getenv("ADMIN_EMAIL", "").strip().lower()
        password = os.getenv("ADMIN_PASSWORD", "")
        if email and password:
            if not EMAIL_RE.match(email):
                raise RuntimeError("ADMIN_EMAIL must be a valid email address.")
            if len(password) < 12:
                raise RuntimeError("ADMIN_PASSWORD must be at least 12 characters long.")
            existing = conn.execute("SELECT id, role, password_hash FROM users WHERE email=?", (email,)).fetchone()
            if existing is None:
                conn.execute(
                    "INSERT INTO users(email, display_name, password_hash, role, is_active, created_at) VALUES(?,?,?,?,1,?)",
                    (email, "Administrator", hash_password(password), "admin", _now()),
                )
            elif existing["role"] != "admin" or not verify_password(password, existing["password_hash"]):
                conn.execute(
                    "UPDATE users SET role='admin',password_hash=?,is_active=1 WHERE id=?",
                    (hash_password(password), existing["id"]),
                )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def public_user(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "email": row["email"],
        "display_name": row["display_name"],
        "role": row["role"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
    }


def create_user(email: str, display_name: str, password: str, role: str = "student") -> dict[str, Any]:
    email = email.strip().lower()
    display_name = display_name.strip()
    if not EMAIL_RE.match(email):
        raise ValueError("Enter a valid email address.")
    if not display_name or len(display_name) > 100:
        raise ValueError("Name must be between 1 and 100 characters.")
    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")
    if role not in ("student", "farmer", "admin"):
        raise ValueError("Invalid account role.")
    with _connection() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users(email, display_name, password_hash, role, is_active, created_at) VALUES(?,?,?,?,1,?)",
                (email, display_name, hash_password(password), role, _now()),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("An account with that email already exists.") from exc
        row = conn.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
        return public_user(row)


def get_user_by_email(email: str):
    with _connection() as conn:
        return conn.execute("SELECT * FROM users WHERE email=? COLLATE NOCASE", (email.strip(),)).fetchone()


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    row = get_user_by_email(email)
    if row is None:
        # A fixed dummy hash keeps the unknown-user path from skipping PBKDF2 entirely.
        dummy = "pbkdf2_sha256$310000$c29tZXNhbHQxMjM0NTY3OA==$dGVzdGRpZ2VzdA=="
        verify_password(password, dummy)
        return None
    if not row["is_active"] or not verify_password(password, row["password_hash"]):
        return None
    return public_user(row)


def create_session(user_id: int) -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with _connection() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (int(time.time()),))
        conn.execute(
            "INSERT INTO sessions(token_hash,user_id,csrf_token,expires_at,created_at) VALUES(?,?,?,?,?)",
            (token_hash, user_id, csrf_token, int(time.time()) + SESSION_TTL_SECONDS, _now()),
        )
    return token, csrf_token


def get_session(token: str | None):
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with _connection() as conn:
        row = conn.execute(
            "SELECT s.csrf_token,s.expires_at,u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=?",
            (token_hash,),
        ).fetchone()
        if row is None:
            return None
        if row["expires_at"] < int(time.time()) or not row["is_active"]:
            conn.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash,))
            return None
        return {"user": public_user(row), "csrf_token": row["csrf_token"], "token_hash": token_hash}


def revoke_session(token: str | None) -> None:
    if not token:
        return
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with _connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash,))


def list_users() -> list[dict[str, Any]]:
    with _connection() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        return [public_user(row) for row in rows]


def set_user_active(user_id: int, is_active: bool) -> bool:
    with _connection() as conn:
        cur = conn.execute("UPDATE users SET is_active=? WHERE id=?", (1 if is_active else 0, user_id))
        if cur.rowcount:
            if not is_active:
                conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
            return True
        return False


def create_farm(owner_user_id: int, data: dict[str, Any]) -> dict[str, Any]:
    farm_id = uuid.uuid4().hex
    now = _now()
    with _connection() as conn:
        conn.execute(
            "INSERT INTO farms(id,owner_user_id,name,location,crop,soil_moisture,temperature_c,humidity_pct,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (farm_id, owner_user_id, data["name"].strip(), data.get("location", "").strip(),
             data.get("crop", "").strip(), data.get("soil_moisture"), data.get("temperature_c"),
             data.get("humidity_pct"), data.get("notes", "").strip(), now, now),
        )
    return get_farm(farm_id)  # type: ignore[return-value]


def get_farm(farm_id: str):
    with _connection() as conn:
        row = conn.execute("SELECT * FROM farms WHERE id=?", (farm_id,)).fetchone()
        return dict(row) if row else None


def list_farms(owner_user_id: int | None = None) -> list[dict[str, Any]]:
    with _connection() as conn:
        if owner_user_id is None:
            rows = conn.execute("SELECT * FROM farms ORDER BY updated_at DESC").fetchall()
        else:
            rows = conn.execute("SELECT * FROM farms WHERE owner_user_id=? ORDER BY updated_at DESC", (owner_user_id,)).fetchall()
        return [dict(row) for row in rows]


def update_farm(farm_id: str, owner_user_id: int | None, data: dict[str, Any]) -> dict[str, Any] | None:
    allowed = {"name", "location", "crop", "soil_moisture", "temperature_c", "humidity_pct", "notes"}
    values = {key: value for key, value in data.items() if key in allowed and value is not None}
    if not values:
        return get_farm(farm_id)
    values["updated_at"] = _now()
    assignments = ",".join(f"{key}=?" for key in values)
    params = [value.strip() if isinstance(value, str) else value for value in values.values()]
    params.append(farm_id)
    sql = f"UPDATE farms SET {assignments} WHERE id=?"
    if owner_user_id is not None:
        sql += " AND owner_user_id=?"
        params.append(owner_user_id)
    with _connection() as conn:
        cur = conn.execute(sql, params)
        if cur.rowcount == 0:
            return None
    return get_farm(farm_id)


def delete_farm(farm_id: str, owner_user_id: int | None) -> bool:
    sql = "DELETE FROM farms WHERE id=?"
    params: list[Any] = [farm_id]
    if owner_user_id is not None:
        sql += " AND owner_user_id=?"
        params.append(owner_user_id)
    with _connection() as conn:
        cur = conn.execute(sql, params)
        return cur.rowcount > 0


init_auth_db()
