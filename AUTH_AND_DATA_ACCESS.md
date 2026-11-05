# Accounts, roles, and data access

## Roles

- **Student:** can register, sign in, upload lecture recordings or YouTube links, process lecturer documents, and view/update/delete only lectures owned by that account.
- **Faculty:** can register, sign in, use the same study tools, and view/update/delete only lectures owned by that account. Faculty accounts do not receive administrator permissions.
- **Farmer (legacy):** existing farmer accounts can still sign in and manage only their own farm records. Farmer is no longer offered in public registration. Farm readings are entered manually; no physical sensor or IoT gateway is connected by this change.
- **Admin:** can view and manage user accounts and access the lecture library. Admin accounts cannot be created by public registration.

The role checks are enforced by FastAPI. Hiding navigation links in the browser is not the security control. Existing lecture registry entries without `owner_user_id` are treated as legacy data and remain visible to admins only until an administrator deliberately migrates/assigns them.

## Local setup

1. Copy `.env.example` to `.env`.
2. Set `ADMIN_EMAIL` and a unique `ADMIN_PASSWORD` of at least 12 characters. Do not commit `.env`.
3. Keep `SESSION_COOKIE_SECURE=0` for local HTTP development only. Set it to `1` behind HTTPS in production.
4. Install the requirements and run `uvicorn api:app --reload --port 8000` from this directory.
5. Open `http://127.0.0.1:8000`. Restart the API after changing the bootstrap admin variables.
6. Sign up through **Create account** for student or faculty accounts. Admins sign in with the bootstrap credentials.

Accounts use PBKDF2 password hashes, random server-side sessions, HttpOnly cookies, SameSite=Strict, session expiry, a CSRF token for state-changing requests, and a bounded per-process login/signup rate limit. Disabling an account revokes its active sessions. API responses also receive basic browser security headers, and API responses are marked `Cache-Control: no-store`.

The API refuses to start when `APP_ENV=production` but `SESSION_COOKIE_SECURE` is not `1`. The supplied Dockerfile sets both production values. Keep `APP_ENV=development` and `SESSION_COOKIE_SECURE=0` only for local HTTP development.

Uploaded DOCX/PPTX ZIP containers are checked for invalid archives, excessive entry counts, and excessive expanded sizes before parsing. Unknown internal processing errors return a generic message to users rather than exposing local paths or provider exception details. Retrieved document text is explicitly treated as untrusted data in the LLM prompt; this is a mitigation, not a guarantee against prompt injection.

## Important production limitations

- Local development defaults to SQLite (`auth.sqlite3`) and ChromaDB (`chroma_db`). For a Cloud Run deployment, this project now includes an optional PostgreSQL + pgvector backend for accounts, sessions, farms, lecture metadata, and indexed chunks. Configure and migrate it using `PHASE5_PART7_CLOUD_RUN.md`; do not assume existing local data has been migrated merely because the backend is enabled.
- Login throttling, model-request limits, processing-job limits, job history, runtime retrievers, summaries, and chat engines are still process-local. They protect one application process but do not enforce global limits across multiple workers or instances. A durable queue/worker and shared rate limiter are required before horizontal scaling.
- Original uploads and generated transcripts are processed from temporary local files and deleted after indexing. PostgreSQL stores indexed chunks, embeddings, and lecture metadata; this revision does not copy original uploads or transcripts to Cloud Storage.
- Configure HTTPS, `SESSION_COOKIE_SECURE=1`, exact `FRONTEND_ORIGINS`, backups, retention/deletion procedures, monitoring, and a password recovery process before a public launch.
- The farm screen stores manual readings and notes; it does not ingest live farm sensor data, verify sensor measurements, or control irrigation hardware.
- Existing lecture registry items without an owner are hidden from students and faculty. Admins can see them. Review legacy entries and assign them only after confirming ownership.
