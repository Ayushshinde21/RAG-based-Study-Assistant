# Phase 5 — Part 6: Security and Reliability

## Changes

### API and browser security
- Added `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy: strict-origin-when-cross-origin` response headers.
- Marked API responses `Cache-Control: no-store` to reduce the risk of authenticated data being retained by shared browser/proxy caches.
- Added a fail-fast configuration check: `APP_ENV=production` requires `SESSION_COOKIE_SECURE=1`.
- Set `APP_ENV=production` in the Docker image; its existing `SESSION_COOKIE_SECURE=1` setting satisfies the check.

### Abuse and resource controls
- Made login/signup attempt tracking thread-safe and bounded, with expired client records removed as new attempts arrive.
- Added a configurable per-authenticated-user rate limit for model-backed chat, summary generation, detailed notes, quiz generation, and admin evaluation.
- Added configurable per-user and per-process limits for active ingestion jobs.
- Bounded retained job history and prune expired/completed jobs when new jobs are created.
- Clean up temporary uploads when job creation is rejected or a worker thread cannot start.
- Mark jobs as failed if their worker thread stops unexpectedly, preventing permanently stuck active-job slots.

### Upload and prompt safety
- Added pre-parse checks for DOCX/PPTX ZIP containers: invalid archives, excessive entry counts, oversized members, and excessive total expanded size are rejected.
- Changed unknown processing errors to safe generic user-facing messages instead of returning raw exception text, local paths, or provider details.
- Strengthened the RAG system prompt to treat retrieved excerpts, questions, and conversation history as untrusted input. This is a mitigation, not a guarantee against prompt injection.

### Test harness reliability
- Converted the existing auth-store and access-control tests from top-level pytest functions to `unittest.TestCase` methods. `python run_tests.py` uses `unittest` discovery, so those eight tests were previously not included in its reported count.
- Added tests for secure-cookie configuration, security headers, safe error messages, login/model request limits, job limits/retention/worker termination, Office ZIP archive bounds, and prompt-injection instructions.

## Configuration added to `.env.example`

- `APP_ENV=development`
- `MAX_ACTIVE_JOBS_PER_USER=2`
- `MAX_ACTIVE_JOBS_TOTAL=12`
- `MAX_RETAINED_JOBS=500`
- `JOB_RETENTION_SECONDS=86400`
- `MODEL_REQUEST_RATE_LIMIT=30`
- `MODEL_REQUEST_WINDOW_SECONDS=60`

Tune these limits to your expected traffic and available compute. Local HTTP development may use `SESSION_COOKIE_SECURE=0`; production must use HTTPS and `SESSION_COOKIE_SECURE=1`.

## Verification performed in the build environment

- 20/20 new security and archive tests passed.
- 87/87 selected security, auth, document, upload, API-session, frontend, retry, audio/video, translation, and source-integrity tests passed.
- Python compilation checks passed for the modified modules and tests.
- The complete `python run_tests.py` suite was attempted. This build environment lacks `langchain_text_splitters`, `langchain_core`, and `langchain_groq`, so six existing test modules could not import. Run the full suite in the project's Windows `.venv` before treating Part 6 as complete.
- Expected full-suite count in the project's fully installed environment: 118 tests (the previous 89 plus 29 newly discovered tests, including eight existing auth/access tests that the old runner skipped).

## Production limitations that remain

- Login and model-request rate limits, job queues/history, chat engines, and runtime retrievers are process-local. They are useful single-process safeguards, not global limits across multiple Uvicorn workers or Cloud Run instances. Use Redis/shared rate limiting and a durable queue/worker system before horizontal scaling.
- SQLite authentication data and ChromaDB indexes remain local-disk stores. Use managed durable storage and a shared database/vector store before multi-instance deployment.
- DOCX/PPTX ZIP limits do not replace malware scanning, PDF resource limits, or independent security testing.
- Prompt instructions reduce prompt-injection risk but do not guarantee that an LLM will always ignore malicious content.
- This patch is a focused application hardening pass, not a formal penetration test or production security certification.
