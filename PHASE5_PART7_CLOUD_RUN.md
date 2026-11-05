# Phase 5 — Part 7: Persistent data and Cloud Run staging

## What changed

- Added an explicit `VECTOR_STORE_BACKEND` switch. Local development continues to use ChromaDB. Cloud Run can use PostgreSQL + pgvector.
- Added a synchronous psycopg connection layer that supports a normal PostgreSQL URL or Cloud SQL Unix socket settings.
- Added durable `study_chunks` and `study_lectures` tables. Vector rows are scoped by both `collection_name` and `owner_user_id`; queries and document reloads use both values.
- Kept the existing embedding model and the dense → BM25 → RRF → CrossEncoder flow. PostgreSQL replaces only the dense-vector persistence backend.
- Added PostgreSQL support for accounts, sessions, and farm records. SQLite remains the default for local development and the existing tests.
- Updated lecture rename and health-check behaviour for the PostgreSQL backend.
- Added non-destructive migration scripts for Chroma collections and SQLite users/farms.
- Added a PowerShell Cloud Run staging deployment script.

## Local development stays unchanged

Leave these settings as shown in `.env.example`:

```dotenv
DATABASE_BACKEND=auto
VECTOR_STORE_BACKEND=chroma
```

With no PostgreSQL connection configured, the app continues to use `auth.sqlite3` and the local `chroma_db` directory.

## PostgreSQL + pgvector configuration

Use PostgreSQL 16 or a supported Cloud SQL for PostgreSQL version with the `vector` extension enabled. The embedding model configured for this index returns 384-dimensional vectors, so keep `VECTOR_DIMENSIONS=384` unless you deliberately change the embedding model and rebuild every vector.

For a local PostgreSQL server, set:

```dotenv
DATABASE_BACKEND=postgres
DATABASE_URL=postgresql://study_admin:URL_ENCODED_PASSWORD@127.0.0.1:5432/study_assistant
VECTOR_STORE_BACKEND=postgres
VECTOR_DIMENSIONS=384
```

For Cloud Run + Cloud SQL, the deployment script uses the Cloud SQL Unix socket. Configure `DB_USER`, `DB_NAME`, `DB_PASSWORD` (Secret Manager), and `INSTANCE_UNIX_SOCKET=/cloudsql/PROJECT:REGION:INSTANCE`. The Cloud Run service must be attached to the same Cloud SQL instance and its service identity needs `roles/cloudsql.client`.

Before first startup, connect to the database using an administrator account and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The app creates its tables and indexes on startup. The database user therefore needs permission to create tables and indexes in the application database. The extension may need to be enabled by a database administrator.

## Migrate existing local data

Stop the local app before migrating. Keep an untouched backup of the current `auth.sqlite3`, `chroma_db`, and `lecture_titles.json` until the Cloud Run copy has been verified.

Set the PostgreSQL connection variables in the PowerShell session, but do not put the password in a command line or commit it to `.env`:

```powershell
$env:DATABASE_BACKEND = "postgres"
$env:VECTOR_STORE_BACKEND = "postgres"
$env:DB_USER = "study_admin"
$env:DB_NAME = "study_assistant"
$env:DB_HOST = "127.0.0.1"
$env:DB_PORT = "5433"
$secure = Read-Host "PostgreSQL password" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try { $env:DB_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr); $secure.Dispose() }
```

Preview the account and farm migration:

```powershell
python .\scripts\migrate_sqlite_auth_to_postgres.py --sqlite-file "C:\path\to\old-project\auth.sqlite3" --dry-run
```

Run the account and farm migration:

```powershell
python .\scripts\migrate_sqlite_auth_to_postgres.py --sqlite-file "C:\path\to\old-project\auth.sqlite3"
```

Existing session tokens are intentionally not copied. Users must sign in again after migration. Password hashes are copied for newly inserted users, so those users do not need password resets. If an email already exists in PostgreSQL with the same role, the migration maps the SQLite ID to that existing account without overwriting its destination password, active status, or profile. Resolve any role conflict before retrying. The migration stores an old-to-new user-ID mapping for lecture ownership migration.

Preview Chroma migration:

```powershell
python .\scripts\migrate_chroma_to_postgres.py --chroma-dir "C:\path\to\old-project\chroma_db" --titles "C:\path\to\old-project\lecture_titles.json" --dry-run
```

Run Chroma migration:

```powershell
python .\scripts\migrate_chroma_to_postgres.py --chroma-dir "C:\path\to\old-project\chroma_db" --titles "C:\path\to\old-project\lecture_titles.json"
```

The script skips collections that already have destination rows for the same owner. Use `--replace` only when you have verified the destination and intentionally want to re-embed those collections; replacement of a collection's rows for that owner is performed in one PostgreSQL transaction. Migration is additive by default; it does not delete or modify the source Chroma database. If a collection has an owner ID, the script requires the SQLite account migration's user-ID mapping rather than guessing an owner.

After migration, test the app against PostgreSQL with `DATABASE_BACKEND=postgres` and `VECTOR_STORE_BACKEND=postgres`. Verify that students can see only their own lectures, admins can see all lectures, and deleting one lecture does not affect another collection.

For a non-destructive database/vector smoke test, set the same connection variables and run:

```powershell
python .\scripts\verify_postgres_backend.py
```

The script creates two temporary student accounts, sessions, farms, and owner-scoped vector records. It verifies PostgreSQL authentication, session revocation, farm ownership, vector similarity search, metadata reload, and cross-owner isolation. It removes its temporary vectors, farms, sessions, and accounts in cleanup code, including when an assertion fails. Do not interrupt the script while its cleanup is running.

## Cloud Run staging deployment

1. Create a Cloud SQL PostgreSQL instance and database. Enable the `vector` extension as described above.
2. Create Secret Manager secrets for the database password, Groq API key, and initial administrator password. The administrator password must be at least 12 characters.
3. Grant the Cloud Run service identity `roles/cloudsql.client` and `roles/secretmanager.secretAccessor`. Grant the deploy/build identity the Cloud Build and Artifact Registry permissions required by your organization.
4. Run `scripts/deploy_cloud_run.ps1` from the project root. Supply the project, Artifact Registry repository, SQL instance connection name, database user/name, and admin email.
5. Check the service URL and `/api/health`. The response should report `database.backend=postgres`, `database.status=connected`, and `vector_store_backend=postgres`.
6. Run account, ownership, upload, chat, source-citation, summary, detailed-notes, quiz, and deletion smoke tests before routing real student traffic.

The script creates a staging-oriented revision with one minimum and one maximum configured instance, request concurrency one, and a 60-minute request timeout. This is intentionally conservative for the app's CPU- and memory-heavy model workloads. It can incur idle-instance charges. Cloud Run's maximum-instance setting is a scaling limit, not a strict distributed lock or a substitute for shared job execution.

## Important remaining release blockers

This change makes accounts, farms, lecture metadata, and vector chunks durable in PostgreSQL. It does **not** yet make every in-process object durable or distributed:

- Ingestion still runs in an in-process daemon thread while the upload request is open. An instance restart, request disconnect, or timeout can interrupt processing. Cloud Run request timeouts are capped at 60 minutes; long-running jobs need a durable worker/queue design with retry and idempotency.
- Job progress, request rate limits, runtime retriever caches, summaries, and chat-engine memory are still process-local. A restart clears those caches; chat history is not durable. Do not scale this revision horizontally until shared rate limiting and a durable worker/job system are implemented and tested.
- The application uses the container's writable filesystem only for temporary audio and upload processing. Those temporary files are deleted after indexing. The durable retained study content is the indexed chunk/vector data and lecture metadata in PostgreSQL; this version does not archive original uploads or transcripts in Cloud Storage.
- `app.py` is the legacy Streamlit interface. The Dockerfile launches the authenticated FastAPI interface. Do not deploy the legacy Streamlit app publicly.

For a public production launch, implement a durable worker/queue (for example Cloud Tasks or Cloud Run Jobs with PostgreSQL-backed job state and Cloud Storage inputs), shared abuse controls, retention/deletion policy verification, and a deployed end-to-end security/browser test. Do not treat this staging package as a horizontal-scale production certification.

## Cloud Run constraints referenced

- Cloud SQL Unix sockets are available at `/cloudsql/INSTANCE_CONNECTION_NAME`; Cloud Run connections require the Cloud SQL attachment and `roles/cloudsql.client`.
- Cloud Run service request timeouts can be configured up to 60 minutes. Requests exceeding the configured timeout return 504; the underlying container code might continue running.
- Cloud Run concurrency should be lowered for CPU/memory-heavy workloads that are not safe to run concurrently.
- Cloud Tasks HTTP target tasks have a maximum task dispatch deadline of 30 minutes. Longer workloads need a different worker design.

Official references:

- Cloud SQL from Cloud Run: https://docs.cloud.google.com/sql/docs/postgres/connect-run
- Cloud Run request timeout: https://docs.cloud.google.com/run/docs/configuring/request-timeout
- Cloud Run concurrency: https://docs.cloud.google.com/run/docs/about-concurrency
- Cloud Tasks HTTP target tasks: https://docs.cloud.google.com/tasks/docs/creating-http-target-tasks
