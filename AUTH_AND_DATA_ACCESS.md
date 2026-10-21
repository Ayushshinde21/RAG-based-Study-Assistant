# Accounts, roles, and data access

## Roles

- **Student:** can register, sign in, upload lecture recordings or YouTube links, process lecturer documents, and view/update/delete only lectures owned by that account.
- **Farmer:** can register, sign in, and create/read/update/delete only farm records owned by that account. Farm readings in this first implementation are entered manually; no physical sensor or IoT gateway is connected by this change.
- **Admin:** can view and manage user accounts and access the lecture library. Farm records are reserved for farmer accounts and are not available in the admin interface or admin API. Admin accounts cannot be created by public registration.

The role checks are enforced by FastAPI. Hiding navigation links in the browser is not the security control. Existing lecture registry entries without `owner_user_id` are treated as legacy data and remain visible to admins only until an administrator deliberately migrates/assigns them.

## Local setup

1. Copy `.env.example` to `.env`.
2. Set `ADMIN_EMAIL` and a unique `ADMIN_PASSWORD` of at least 12 characters. Do not commit `.env`.
3. Keep `SESSION_COOKIE_SECURE=0` for local HTTP development only. Set it to `1` behind HTTPS in production.
4. Install the requirements and run `uvicorn api:app --reload --port 8000` from this directory.
5. Open `http://127.0.0.1:8000`. Restart the API after changing the bootstrap admin variables.
6. Sign up through **Create account** for student or farmer accounts. Admins sign in with the bootstrap credentials.

Accounts use PBKDF2 password hashes, random server-side sessions, HttpOnly cookies, SameSite=Strict, session expiry, a CSRF token for state-changing requests, and a basic per-process login/signup rate limit. Disabling an account revokes its active sessions.

## Important production limitations

- `auth.sqlite3` is a local SQLite database. Use a managed, durable database when running multiple instances or a serverless platform. Do not rely on container-local disk for important records.
- Lecture metadata and vectors are currently stored by the existing Chroma registry on local disk. Production requires shared durable storage and consistent ownership metadata across all instances.
- Configure HTTPS, `SESSION_COOKIE_SECURE=1`, exact `FRONTEND_ORIGINS`, backups, retention/deletion procedures, monitoring, and a password recovery process before a public launch.
- The farm screen stores manual readings and notes; it does not ingest live farm sensor data, verify sensor measurements, or control irrigation hardware.
- Existing lecture registry items without an owner are hidden from students. Admins can see them. Review legacy entries and assign them only after confirming ownership.
