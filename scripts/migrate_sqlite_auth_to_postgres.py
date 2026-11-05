from __future__ import annotations
import argparse
import os
import sqlite3

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
except ImportError:
    pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy users and farms from the local auth SQLite database to PostgreSQL."
    )
    parser.add_argument("--sqlite-file", default=os.getenv("AUTH_DB_PATH", "auth.sqlite3"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.dry_run:
        os.environ["DATABASE_BACKEND"] = "postgres"
        has_url = bool(os.getenv("DATABASE_URL", "").strip())
        has_fields = all(os.getenv(key, "").strip() for key in ("DB_USER", "DB_PASSWORD", "DB_NAME"))
        if not (has_url or has_fields):
            raise SystemExit("Configure DATABASE_URL or DB_USER, DB_PASSWORD, and DB_NAME before running this migration.")
        try:
            import auth_store
            from storage.database import postgres_connection
        except ImportError as exc:
            raise SystemExit(f"A project dependency is missing: {exc}") from exc
    else:
        postgres_connection = None
        auth_store = None

    source_path = os.path.abspath(args.sqlite_file)
    if not os.path.isfile(source_path):
        raise SystemExit(f"SQLite database not found: {source_path}")

    if not args.dry_run:
        auth_store.init_auth_db()
    source = sqlite3.connect(source_path)
    source.row_factory = sqlite3.Row
    try:
        users = source.execute(
            "SELECT id,email,display_name,password_hash,role,is_active,created_at FROM users ORDER BY id"
        ).fetchall()
        farms_table = source.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='farms'"
        ).fetchone()
        farms = source.execute(
            "SELECT id,owner_user_id,name,location,crop,soil_moisture,temperature_c,humidity_pct,notes,created_at,updated_at FROM farms ORDER BY id"
        ).fetchall() if farms_table else []
    finally:
        source.close()

    if args.dry_run:
        print(f"DRY RUN: would migrate {len(users)} users and {len(farms)} farms.")
        print("Existing sessions are intentionally not copied; all users will sign in again.")
        return 0

    user_id_map: dict[int, int] = {}
    with postgres_connection() as conn:
        for user in users:
            existing = conn.execute(
                "SELECT id,role FROM users WHERE lower(email)=lower(%s)",
                (user["email"],),
            ).fetchone()
            if existing:
                if existing["role"] != user["role"]:
                    raise RuntimeError(
                        f"Email {user['email']} already exists in PostgreSQL with role "
                        f"{existing['role']!r}, but the SQLite account has role {user['role']!r}. "
                        "Resolve the account conflict before retrying."
                    )
                user_id_map[int(user["id"])] = int(existing["id"])
                continue

            id_conflict = conn.execute(
                "SELECT id FROM users WHERE id=%s",
                (int(user["id"]),),
            ).fetchone()
            if id_conflict:
                inserted = conn.execute(
                    """INSERT INTO users(email,display_name,password_hash,role,is_active,created_at)
                       VALUES(%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (user["email"], user["display_name"], user["password_hash"], user["role"], bool(user["is_active"]), user["created_at"]),
                ).fetchone()
            else:
                inserted = conn.execute(
                    """INSERT INTO users(id,email,display_name,password_hash,role,is_active,created_at)
                       VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (int(user["id"]), user["email"], user["display_name"], user["password_hash"], user["role"], bool(user["is_active"]), user["created_at"]),
                ).fetchone()
            user_id_map[int(user["id"])] = int(inserted["id"])

        for source_id, target_id in user_id_map.items():
            conn.execute(
                """INSERT INTO migration_user_id_map(source_user_id,target_user_id)
                   VALUES(%s,%s)
                   ON CONFLICT (source_user_id) DO UPDATE SET target_user_id=EXCLUDED.target_user_id""",
                (source_id, target_id),
            )

        for farm in farms:
            mapped_owner = user_id_map.get(int(farm["owner_user_id"]))
            if mapped_owner is None:
                raise RuntimeError(
                    f"Farm {farm['id']} references user {farm['owner_user_id']}, "
                    "but no migrated user-ID mapping exists."
                )
            existing_farm = conn.execute(
                "SELECT owner_user_id FROM farms WHERE id=%s",
                (farm["id"],),
            ).fetchone()
            if existing_farm:
                if int(existing_farm["owner_user_id"]) != mapped_owner:
                    raise RuntimeError(
                        f"Farm ID collision for {farm['id']}: the destination record belongs "
                        "to a different user. Resolve this conflict before retrying."
                    )
                continue
            conn.execute(
                """INSERT INTO farms(id,owner_user_id,name,location,crop,soil_moisture,temperature_c,
                   humidity_pct,notes,created_at,updated_at)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    farm["id"], mapped_owner, farm["name"], farm["location"], farm["crop"],
                    farm["soil_moisture"], farm["temperature_c"], farm["humidity_pct"],
                    farm["notes"], farm["created_at"], farm["updated_at"],
                ),
            )
        conn.execute(
            "SELECT setval(pg_get_serial_sequence('users','id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM users"
        )

    print(f"Migration complete. users_processed={len(users)}, farms_processed={len(farms)}.")
    print("Existing sessions were not copied; users must sign in again.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
