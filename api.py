"""
Campus Study Desk - FastAPI backend.

Put this file in the project root, next to main.py / core / utils / features,
so the existing imports and the chroma_db/ and transcripts/ folders keep working.

Run locally:   uvicorn api:app --reload --port 8000
API docs:      http://127.0.0.1:8000/docs
"""
import gc
import json
import logging
import os
import re
import tempfile
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

import auth_store

ALLOWED_EXTENSIONS = {"mp4", "mkv", "avi", "mov", "webm", "mp3", "wav", "m4a", "ogg", "flac"}
REFERENCE_EXTENSIONS = {"pdf", "docx", "pptx", "txt", "md"}
# Cloud Run rejects HTTP/1 request bodies over 32 MiB, so the hosted default is 30.
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "200"))
MAX_REFERENCE_FILE_MB = int(os.getenv("MAX_REFERENCE_FILE_MB", "15"))
MAX_REFERENCE_FILES = 5
MAX_DOCUMENT_FILES = int(os.getenv("MAX_DOCUMENT_FILES", "5"))
MAX_DOCUMENT_FILE_MB = int(os.getenv("MAX_DOCUMENT_FILE_MB", str(MAX_REFERENCE_FILE_MB)))
MAX_DOCUMENT_TEXT_CHARS = int(os.getenv("MAX_DOCUMENT_TEXT_CHARS", "250000"))
MAX_REFERENCE_TEXT_CHARS = 250_000
YT_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be", "www.youtu.be"}
TITLES_PATH = "lecture_titles.json"
# YouTube blocks downloads from cloud servers (HTTP 403), so the hosted build sets this to 0.
YOUTUBE_ENABLED = os.getenv("YOUTUBE_ENABLED", "1") == "1"

@asynccontextmanager
async def lifespan(_app):
    # On Cloud Run (WARMUP=1) load every model before the first request,
    # so the first user doesn't wait for them. Skipped locally for fast reloads.
    if os.getenv("WARMUP") == "1":
        import utils.transcriber  # noqa: F401  (loads Whisper)
        import core.reranker      # noqa: F401  (loads the CrossEncoder)
        from core.vector_store import get_embeddings
        get_embeddings()
    yield


app = FastAPI(title="Campus Study Desk API", lifespan=lifespan)

origins = [o.strip() for o in os.getenv(
    "FRONTEND_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500"
).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
    allow_credentials=True,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


SESSION_COOKIE = "campus_session"
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
LOGIN_ATTEMPTS: dict[str, list[float]] = {}
LOGIN_RATE_WINDOW_SECONDS = 300
LOGIN_RATE_LIMIT = 12
MAX_TRACKED_AUTH_CLIENTS = 10_000
LOGIN_ATTEMPT_LOCK = threading.Lock()
MODEL_REQUESTS: dict[int, list[float]] = {}
MODEL_REQUEST_WINDOW_SECONDS = max(10, int(os.getenv("MODEL_REQUEST_WINDOW_SECONDS", "60")))
MODEL_REQUEST_RATE_LIMIT = max(1, int(os.getenv("MODEL_REQUEST_RATE_LIMIT", "30")))
MAX_TRACKED_MODEL_USERS = 10_000
MODEL_REQUEST_LOCK = threading.Lock()
LOGGER = logging.getLogger("campus_study_desk")

MAX_ACTIVE_JOBS_PER_USER = max(1, int(os.getenv("MAX_ACTIVE_JOBS_PER_USER", "2")))
MAX_ACTIVE_JOBS_TOTAL = max(1, int(os.getenv("MAX_ACTIVE_JOBS_TOTAL", "12")))
MAX_RETAINED_JOBS = max(20, int(os.getenv("MAX_RETAINED_JOBS", "500")))
JOB_RETENTION_SECONDS = max(3600, int(os.getenv("JOB_RETENTION_SECONDS", "86400")))
JOB_LOCK = threading.RLock()


def validate_session_cookie_security(app_environment: str, secure_cookie: bool) -> None:
    """Fail closed if a production deployment would issue non-Secure cookies."""
    if app_environment in {"prod", "production"} and not secure_cookie:
        raise RuntimeError(
            "SESSION_COOKIE_SECURE=1 is required when APP_ENV is production."
        )


validate_session_cookie_security(APP_ENV, SESSION_COOKIE_SECURE)


def allow_auth_attempt(client_id: str, now: float | None = None) -> bool:
    """Bounded per-process auth throttle; use shared storage for multi-instance deployments."""
    current = time.time() if now is None else now
    key = (client_id or "unknown")[:128]
    cutoff = current - LOGIN_RATE_WINDOW_SECONDS
    with LOGIN_ATTEMPT_LOCK:
        for known_key, timestamps in list(LOGIN_ATTEMPTS.items()):
            active = [stamp for stamp in timestamps if stamp > cutoff]
            if active:
                LOGIN_ATTEMPTS[known_key] = active
            else:
                LOGIN_ATTEMPTS.pop(known_key, None)

        attempts = LOGIN_ATTEMPTS.get(key, [])
        if len(attempts) >= LOGIN_RATE_LIMIT:
            return False
        attempts.append(current)
        LOGIN_ATTEMPTS[key] = attempts

        if len(LOGIN_ATTEMPTS) > MAX_TRACKED_AUTH_CLIENTS:
            oldest_keys = sorted(
                LOGIN_ATTEMPTS,
                key=lambda item: LOGIN_ATTEMPTS[item][-1] if LOGIN_ATTEMPTS[item] else 0,
            )
            for old_key in oldest_keys[: len(LOGIN_ATTEMPTS) - MAX_TRACKED_AUTH_CLIENTS]:
                LOGIN_ATTEMPTS.pop(old_key, None)
    return True


def clear_auth_attempts(client_id: str) -> None:
    key = (client_id or "unknown")[:128]
    with LOGIN_ATTEMPT_LOCK:
        LOGIN_ATTEMPTS.pop(key, None)


def enforce_model_request_limit(user_id: int, now: float | None = None) -> None:
    """Bound model-backed requests per authenticated user within this process."""
    current = time.time() if now is None else now
    cutoff = current - MODEL_REQUEST_WINDOW_SECONDS
    user_key = int(user_id)
    with MODEL_REQUEST_LOCK:
        for known_user, timestamps in list(MODEL_REQUESTS.items()):
            active = [stamp for stamp in timestamps if stamp > cutoff]
            if active:
                MODEL_REQUESTS[known_user] = active
            else:
                MODEL_REQUESTS.pop(known_user, None)

        attempts = MODEL_REQUESTS.get(user_key, [])
        if len(attempts) >= MODEL_REQUEST_RATE_LIMIT:
            raise HTTPException(
                429,
                "You've reached the AI request limit. Wait a moment before trying again.",
            )
        attempts.append(current)
        MODEL_REQUESTS[user_key] = attempts

        if len(MODEL_REQUESTS) > MAX_TRACKED_MODEL_USERS:
            oldest_users = sorted(
                MODEL_REQUESTS,
                key=lambda item: MODEL_REQUESTS[item][-1] if MODEL_REQUESTS[item] else 0,
            )
            for old_user in oldest_users[: len(MODEL_REQUESTS) - MAX_TRACKED_MODEL_USERS]:
                MODEL_REQUESTS.pop(old_user, None)


def current_user(request: Request) -> dict:
    session = auth_store.get_session(request.cookies.get(SESSION_COOKIE))
    if not session:
        raise HTTPException(status_code=401, detail="Please sign in to continue.")
    request.state.csrf_token = session["csrf_token"]
    return session["user"]


def require_roles(*roles: str):
    def dependency(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Your account does not have permission to do that.")
        return user
    return dependency


STUDENT_OR_ADMIN = require_roles("student", "admin")
FARMER_ONLY = require_roles("farmer")
ADMIN_ONLY = require_roles("admin")


@app.middleware("http")
async def csrf_guard(request: Request, call_next):
    if request.method in {"POST", "PATCH", "DELETE", "PUT"} and request.url.path.startswith("/api/"):
        public_auth_routes = {"/api/auth/login", "/api/auth/register"}
        if request.url.path not in public_auth_routes and request.cookies.get(SESSION_COOKIE):
            session = auth_store.get_session(request.cookies.get(SESSION_COOKIE))
            supplied = request.headers.get("x-csrf-token", "")
            if not session or not supplied or not secrets_compare(supplied, session["csrf_token"]):
                return JSONResponse(status_code=403, content={"detail": "Your security token is missing or expired. Refresh the page and try again."})
    return await call_next(request)


def secrets_compare(left: str, right: str) -> bool:
    import hmac
    return hmac.compare_digest(left, right)


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE, token, max_age=auth_store.SESSION_TTL_SECONDS,
        httponly=True, secure=SESSION_COOKIE_SECURE, samesite="strict", path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True,
                           secure=SESSION_COOKIE_SECURE, samesite="strict")


def lecture_belongs_to_user(lecture: dict, user: dict) -> bool:
    if user["role"] == "admin":
        return True
    if user["role"] != "student":
        return False
    try:
        return lecture.get("owner_user_id") is not None and int(lecture["owner_user_id"]) == int(user["id"])
    except (TypeError, ValueError):
        return False


def require_lecture_access(lecture_id: str, user: dict) -> dict:
    from core.vector_store import get_lecture
    lecture = get_lecture(lecture_id)
    if not lecture or not lecture_belongs_to_user(lecture, user):
        # Use 404 rather than confirming that another user's lecture exists.
        raise HTTPException(404, "Lecture not found")
    return lecture

# ── In-memory state (replaces st.session_state) ──────────────────────────────
JOBS: dict[str, dict] = {}                 # job_id -> progress of a processing run
RUNTIME: dict[str, dict] = {}              # lecture_id -> {docs, dense, bm25} (shared retrievers)
ENGINES: dict[tuple, object] = {}          # (lecture_id, user_id, session_id) -> isolated RAGEngine
SUMMARIES: dict[str, str] = {}
DETAILED_NOTES: dict[str, str] = {}
PROCESS_LOCK = threading.Semaphore(1)      # one heavy pipeline at a time (protects RAM)
LOAD_LOCK = threading.Lock()
TITLE_LOCK = threading.Lock()
ENGINE_LOCK = threading.RLock()
MAX_ENGINES = 200


# ── Helpers ──────────────────────────────────────────────────────────────────
def redact(text) -> str:
    text = str(text)
    for name, value in os.environ.items():
        if value and len(value) >= 8 and any(t in name.upper() for t in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
            text = text.replace(value, "[hidden]")
    return text


def friendly_error(exc: Exception) -> str:
    """Return a safe user-facing message without exposing paths, prompts, or provider details."""
    msg = redact(exc)
    low = msg.lower()

    if "403" in msg or "forbidden" in low:
        return "The download was refused (HTTP 403). Try another video, or upload the recording as a file."
    if "api key" in low or "api_key" in low or "401" in msg or "unauthorized" in low:
        return "The AI service rejected the request. Check the API keys on the server."
    if "rate limit" in low or "429" in msg or "quota" in low:
        return "The AI service rate limit was reached. Please wait a moment and try again."
    if "ffmpeg" in low:
        return "Audio processing could not start. Verify that FFmpeg is installed and available on the server."
    if "no audio could be extracted" in low:
        return "No audio could be extracted from this recording. Try another file or format."
    if "nearly empty" in low or "recording may be silent" in low or "transcription came back empty" in low:
        return "No usable speech was detected. Check that the recording contains clear audio and try again."
    if "ocr is required" in low or "scanned or image-only" in low:
        return "This PDF contains no selectable text. OCR is required before it can be indexed."
    if "no documents could be indexed" in low:
        return "No documents could be indexed. Check that the uploaded files contain readable text."
    if "no readable text" in low or "no readable document text" in low or "no searchable chunks" in low:
        return "No readable document text was found. Check the file and try again."
    if "unsupported document format" in low or "unsupported file type" in low:
        return "This document format is not supported. Upload a PDF, DOCX, PPTX, TXT, or Markdown file."
    if "youtube audio downloading is disabled" in low:
        return "This server cannot download YouTube audio. Try a video with captions or upload the recording."

    LOGGER.warning("Suppressed internal error details (%s)", exc.__class__.__name__)
    return "An unexpected processing error occurred. Please try again. If it continues, contact support."


def valid_youtube_url(url: str) -> bool:
    url = (url or "").strip()
    if not url or len(url) > 500 or re.search(r"\s", url):
        return False
    try:
        p = urlparse(url)
        host = (p.hostname or "").lower()
    except ValueError:
        return False
    if p.scheme not in ("http", "https") or host not in YT_HOSTS:
        return False
    if host.endswith("youtu.be"):
        return bool(p.path.strip("/"))
    return bool(parse_qs(p.query).get("v")) or p.path.startswith(("/shorts/", "/embed/", "/live/"))


def load_titles() -> dict:
    try:
        with open(TITLES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_titles(titles: dict):
    with open(TITLES_PATH, "w", encoding="utf-8") as f:
        json.dump(titles, f, indent=2)


def with_title(lecture: dict) -> dict:
    out = dict(lecture)
    out["title"] = load_titles().get(lecture["id"], lecture.get("title", "Untitled lecture"))
    return out


def get_runtime(lecture_id: str) -> dict:
    """Load a saved lecture's retrievers on first use (same as open_lecture in app.py)."""
    rt = RUNTIME.get(lecture_id)
    if rt:
        return rt
    from core.vector_store import get_lecture, load_vector_store, get_all_docs_from_store, get_dense_retriever
    from core.bm25_index import build_bm25_retriever

    lecture = get_lecture(lecture_id)
    if not lecture:
        raise HTTPException(404, "Lecture not found")
    with LOAD_LOCK:
        rt = RUNTIME.get(lecture_id)
        if rt:
            return rt
        try:
            vs = load_vector_store(lecture["collection_name"])
            docs = get_all_docs_from_store(vs)
            if not docs:
                raise RuntimeError("The saved index for this lecture is empty or missing.")
            rt = {"docs": docs, "dense": get_dense_retriever(vs, k=10), "bm25": build_bm25_retriever(docs, k=10)}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"Couldn't open this lecture. {friendly_error(e)}")
        RUNTIME[lecture_id] = rt
    return rt


def get_engine(lecture_id: str, session_id: str, user_id: int):
    """Return a chat engine isolated to one authenticated user and session."""
    key = (str(lecture_id), int(user_id), session_id)
    with ENGINE_LOCK:
        eng = ENGINES.get(key)
        if eng is None:
            from core.rag_engine import RAGEngine
            rt = get_runtime(lecture_id)
            eng = RAGEngine(rt["dense"], rt["bm25"])
            if len(ENGINES) >= MAX_ENGINES:
                ENGINES.pop(next(iter(ENGINES)))
            ENGINES[key] = eng
        return eng


# ── Processing pipeline (process_uploaded_file from app.py, minus Streamlit) ─
STEPS = ["Extracting audio", "Transcribing lecture", "Chunking transcript",
         "Building search index", "Warming up reranker", "Saving to library"]


def set_step(job: dict, i: int):
    job["step"], job["stage"] = i + 1, STEPS[i]


def finish_job(job_id: str, **updates) -> None:
    """Publish a terminal job state atomically for pollers and queue accounting."""
    with JOB_LOCK:
        job = JOBS.get(job_id)
        if job is not None:
            job.update(updates)
            job["finished_at"] = time.time()


def run_job(
    job_id: str,
    source: str,
    is_url: bool,
    owner_user_id: int,
    reference_files: list[dict] | None = None,
    display_title: str | None = None,
):
    job = JOBS[job_id]
    reference_files = reference_files or []
    job.setdefault("warnings", [])
    audio_path = None
    vector_store = None
    lecture_id = None
    job["status"] = "queued"
    try:
        with PROCESS_LOCK:
            job["status"] = "running"

            video_title = None
            transcript_path = None
            set_step(job, 0)

            # Captions are far cheaper than speech recognition for multi-hour YouTube videos.
            # If English captions are unavailable, continue with the normal audio pipeline.
            if is_url:
                job["stage"] = "Checking for YouTube captions"
                try:
                    from utils.audio_processor import download_youtube_captions
                    caption_result = download_youtube_captions(source)
                except Exception as e:
                    print(f"[job {job_id}] caption-first processing skipped: {friendly_error(e)}")
                    caption_result = None

                if caption_result:
                    from utils.transcriber import save_transcript
                    segments, video_title = caption_result
                    safe_title = re.sub(r"[^A-Za-z0-9._-]+", "_", video_title).strip("._")[:150] or "YouTube_lecture"
                    transcript_path = save_transcript(segments, os.path.join("audio_files", safe_title + ".mp3"))
                    del segments
                    gc.collect()
                    job["step"] = 2
                    job["stage"] = "YouTube captions ready"

            if transcript_path is None:
                if is_url and not YOUTUBE_ENABLED:
                    raise RuntimeError(
                        "No usable English YouTube captions were available. This server has YouTube audio downloading disabled. "
                        "Try a video with English captions or run the project locally with YOUTUBE_ENABLED=1."
                    )
                set_step(job, 0)
                from utils.audio_processor import get_audio_path
                audio_path = get_audio_path(source)
                if not audio_path or not os.path.exists(audio_path):
                    raise RuntimeError("No audio could be extracted from this source.")
                size = os.path.getsize(audio_path)
                print(f"[job {job_id}] audio file: {audio_path} ({size / 1024:.0f} KB)")
                if size < 2048:
                    raise RuntimeError(
                        f"The audio file is nearly empty ({size} bytes). YouTube probably "
                        "cut the download. Try again, try another video, or upload the file."
                    )

                set_step(job, 1)
                from utils.transcriber import transcribe_with_timestamps, save_transcript
                def transcription_progress(message: str):
                    job["stage"] = message
                segments = transcribe_with_timestamps(audio_path, progress_callback=transcription_progress)
                if not segments:
                    raise RuntimeError("The transcription came back empty. The recording may be silent.")
                transcript_path = save_transcript(segments, audio_path)
                del segments
                gc.collect()

            set_step(job, 2)
            from core.chunker import chunk_from_file
            docs = chunk_from_file(transcript_path, method="semantic")
            if not docs:
                raise RuntimeError("No text chunks could be created from the transcript.")
            for doc in docs:
                doc.metadata["source_type"] = "lecture_transcript"

            # Lecturer-provided material is optional. A malformed attachment should
            # not prevent a valid lecture recording from being processed.
            if reference_files:
                from core.chunker import chunk_text
                for index, item in enumerate(reference_files, start=1):
                    try:
                        job["stage"] = f"Reading lecturer material {index} of {len(reference_files)}"
                        text = extract_reference_text(item["path"], item["filename"])
                        if not text.strip():
                            raise ValueError("No readable text was found in this file.")
                        if len(text) > MAX_REFERENCE_TEXT_CHARS:
                            text = text[:MAX_REFERENCE_TEXT_CHARS]
                            job["warnings"].append(
                                f"{item['filename']}: only the first {MAX_REFERENCE_TEXT_CHARS:,} characters were indexed."
                            )
                        material_docs = chunk_text(text, source=item["filename"], method="fixed")
                        for chunk_index, doc in enumerate(material_docs):
                            doc.metadata.update({
                                "source_type": "lecturer_material",
                                "filename": item["filename"],
                                "document_chunk": chunk_index,
                            })
                        docs.extend(material_docs)
                    except Exception as e:
                        warning = f"Could not read {item['filename']}: {friendly_error(e)}"
                        job["warnings"].append(warning)
                        print(f"[job {job_id}] {warning}")

            set_step(job, 3)
            from core.vector_store import (build_vector_store, get_dense_retriever,
                                           new_collection_name, register_lecture)
            from core.bm25_index import build_bm25_retriever
            collection = new_collection_name()
            vector_store = build_vector_store(docs, reset=True, collection_name=collection)
            dense = get_dense_retriever(vector_store, k=10)
            bm25 = build_bm25_retriever(docs, k=10)

            set_step(job, 4)
            import core.reranker  # noqa: F401  (import loads the model)

            set_step(job, 5)
            fallback_source = audio_path or source
            title = video_title or display_title or os.path.splitext(os.path.basename(fallback_source))[0]
            lecture_id = register_lecture(title=title, collection_name=collection,
                                          num_chunks=len(docs), transcript_path=transcript_path,
                                          owner_user_id=owner_user_id)
            RUNTIME[lecture_id] = {"docs": docs, "dense": dense, "bm25": bm25}

        finish_job(job_id, status="done", lecture_id=lecture_id, stage="Workspace ready")
    except Exception as e:
        if lecture_id is None and vector_store is not None:
            try:
                vector_store.delete_collection()
            except Exception:
                pass
        finish_job(
            job_id,
            status="error",
            error=f"Processing failed during {job.get('stage', 'startup')}. {friendly_error(e)}",
        )
    finally:
        paths_to_remove = {source if not is_url else None, audio_path}
        paths_to_remove.update(item.get("path") for item in reference_files)
        for p in paths_to_remove:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


def run_document_job(job_id: str, uploaded_files: list[dict], owner_user_id: int):
    """Build a searchable study workspace directly from uploaded documents."""
    job = JOBS[job_id]
    job.update(status="queued", step=0, total=4, stage="Waiting to start")
    vector_store = None
    lecture_id = None
    collection_name = None
    uploaded_files = uploaded_files or []

    try:
        with PROCESS_LOCK:
            job.update(status="running", step=1, stage="Extracting documents")
            from core.chunker import chunk_text

            all_docs = []
            indexed_filenames = []
            batch_id = uuid.uuid4().hex[:12]

            for index, item in enumerate(uploaded_files, start=1):
                filename = item["filename"]
                try:
                    job.update(
                        step=1,
                        stage=f"Extracting document {index} of {len(uploaded_files)}: {filename}",
                    )
                    text = extract_reference_text(item["path"], filename)
                    if len(text) > MAX_DOCUMENT_TEXT_CHARS:
                        text = text[:MAX_DOCUMENT_TEXT_CHARS]
                        job["warnings"].append(
                            f"{filename}: only the first {MAX_DOCUMENT_TEXT_CHARS:,} characters were indexed."
                        )

                    job.update(
                        step=2,
                        stage=f"Cleaning and chunking document {index} of {len(uploaded_files)}",
                    )
                    chunks = chunk_text(text, source=filename, method="fixed")
                    if not chunks:
                        raise RuntimeError("No searchable chunks were created.")

                    document_id = uuid.uuid4().hex[:12]
                    extension = os.path.splitext(filename)[1].lower().lstrip(".")
                    for chunk_index, doc in enumerate(chunks):
                        doc.metadata.update({
                            "source_type": "uploaded_document",
                            "filename": filename,
                            "document_type": extension,
                            "document_id": document_id,
                            "document_chunk": chunk_index,
                            "ingestion_batch_id": batch_id,
                        })
                    all_docs.extend(chunks)
                    indexed_filenames.append(filename)
                except Exception as exc:
                    warning = f"Could not index {filename}: {friendly_error(exc)}"
                    job["warnings"].append(warning)
                    print(f"[job {job_id}] {warning}")

            if not all_docs:
                details = " ".join(job.get("warnings", []))
                raise RuntimeError(
                    "No documents could be indexed. " + details
                    if details else "No readable document content was found."
                )

            job.update(step=3, stage="Building the searchable document index")
            from core.vector_store import (
                build_vector_store,
                delete_collection,
                get_dense_retriever,
                new_collection_name,
                register_lecture,
            )
            from core.bm25_index import build_bm25_retriever

            collection_name = new_collection_name()
            vector_store = build_vector_store(
                all_docs,
                reset=True,
                collection_name=collection_name,
            )
            dense = get_dense_retriever(vector_store, k=10)
            bm25 = build_bm25_retriever(all_docs, k=10)

            job.update(step=4, stage="Saving the document study workspace")
            stems = [os.path.splitext(name)[0] for name in indexed_filenames]
            if len(stems) == 1:
                title = stems[0]
            else:
                preview = ", ".join(stems[:2])
                suffix = f" + {len(stems) - 2} more" if len(stems) > 2 else ""
                title = f"{len(stems)} documents: {preview}{suffix}"
            title = title[:200] or "Uploaded documents"

            lecture_id = register_lecture(
                title=title,
                collection_name=collection_name,
                num_chunks=len(all_docs),
                transcript_path=None,
                owner_user_id=owner_user_id,
                content_type="documents",
                source_files=indexed_filenames,
            )
            RUNTIME[lecture_id] = {
                "docs": all_docs,
                "dense": dense,
                "bm25": bm25,
            }

        finish_job(
            job_id,
            status="done",
            lecture_id=lecture_id,
            stage="Document workspace ready",
            indexed_files=indexed_filenames,
            num_chunks=len(all_docs),
        )
    except Exception as exc:
        if collection_name and lecture_id is None:
            try:
                if vector_store is not None:
                    vector_store.delete_collection()
                else:
                    delete_collection(collection_name)
            except Exception:
                pass
            RUNTIME.pop(collection_name, None)
        finish_job(
            job_id,
            status="error",
            error=f"Document processing failed during {job.get('stage', 'startup')}. {friendly_error(exc)}",
        )
    finally:
        for item in uploaded_files:
            path = item.get("path")
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


def _prune_jobs_locked(now: float) -> None:
    """Remove expired completed jobs and keep the in-memory job registry bounded."""
    terminal = {"done", "error"}
    for job_id, job in list(JOBS.items()):
        if job.get("status") not in terminal:
            continue
        finished = float(job.get("finished_at", job.get("created_at", now)))
        if now - finished >= JOB_RETENTION_SECONDS:
            JOBS.pop(job_id, None)

    if len(JOBS) >= MAX_RETAINED_JOBS:
        completed = sorted(
            (
                (float(job.get("finished_at", job.get("created_at", now))), job_id)
                for job_id, job in JOBS.items()
                if job.get("status") in terminal
            ),
            key=lambda item: item[0],
        )
        while len(JOBS) >= MAX_RETAINED_JOBS and completed:
            _, old_job_id = completed.pop(0)
            JOBS.pop(old_job_id, None)


def new_job(owner_user_id: int | None = None) -> str:
    now = time.time()
    with JOB_LOCK:
        _prune_jobs_locked(now)
        active_jobs = [
            job for job in JOBS.values()
            if job.get("status") in {"queued", "running"}
        ]
        if len(active_jobs) >= MAX_ACTIVE_JOBS_TOTAL:
            raise HTTPException(429, "The processing queue is full. Wait for a current job to finish and try again.")
        if owner_user_id is not None:
            user_active = sum(
                1 for job in active_jobs
                if job.get("owner_user_id") == owner_user_id
            )
            if user_active >= MAX_ACTIVE_JOBS_PER_USER:
                raise HTTPException(429, "You already have the maximum number of active processing jobs. Wait for one to finish.")
        if len(JOBS) >= MAX_RETAINED_JOBS:
            raise HTTPException(503, "The job registry is temporarily full. Try again after existing jobs finish.")

        job_id = uuid.uuid4().hex[:12]
        JOBS[job_id] = {
            "status": "queued",
            "stage": "Waiting to start",
            "step": 0,
            "total": len(STEPS),
            "lecture_id": None,
            "error": None,
            "warnings": [],
            "owner_user_id": owner_user_id,
            "created_at": now,
        }
        return job_id


def _remove_temporary_uploads(items: list[dict] | None) -> None:
    for item in items or []:
        path = item.get("path")
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


def start_document_job(uploaded_files: list[dict], owner_user_id: int):
    try:
        job_id = new_job(owner_user_id)
    except Exception:
        _remove_temporary_uploads(uploaded_files)
        raise
    with JOB_LOCK:
        JOBS[job_id]["total"] = 4
    thread = threading.Thread(
        target=run_document_job,
        args=(job_id, uploaded_files, owner_user_id),
        daemon=True,
    )
    try:
        thread.start()
    except Exception:
        with JOB_LOCK:
            JOBS.pop(job_id, None)
        _remove_temporary_uploads(uploaded_files)
        raise
    return job_id, thread


def start_job(
    source: str,
    is_url: bool,
    owner_user_id: int,
    reference_files: list[dict] | None = None,
    display_title: str | None = None,
):
    try:
        job_id = new_job(owner_user_id)
    except Exception:
        _remove_temporary_uploads(reference_files)
        if not is_url and source and os.path.exists(source):
            try:
                os.remove(source)
            except OSError:
                pass
        raise
    thread = threading.Thread(
        target=run_job,
        args=(job_id, source, is_url, owner_user_id, reference_files, display_title),
        daemon=True,
    )
    try:
        thread.start()
    except Exception:
        with JOB_LOCK:
            JOBS.pop(job_id, None)
        _remove_temporary_uploads(reference_files)
        if not is_url and source and os.path.exists(source):
            try:
                os.remove(source)
            except OSError:
                pass
        raise
    return job_id, thread


def uploaded_lecture_title(filename: str | None) -> str:
    """Return a safe display title from the original uploaded filename."""
    supplied = (filename or "").replace("\\", "/")
    basename = os.path.basename(supplied)
    title = os.path.splitext(basename)[0].strip()
    return title or "Uploaded lecture"


def job_events(job_id: str, thread: threading.Thread):
    """
    Streams progress as newline-delimited JSON for as long as the job runs.
    The work happens inside this open request on purpose: Cloud Run only gives
    the container CPU while a request is being served.
    """
    last, last_beat = None, time.time()
    while True:
        with JOB_LOCK:
            job = dict(JOBS[job_id])
        alive = thread.is_alive()
        if not alive and job.get("status") not in {"done", "error"}:
            with JOB_LOCK:
                current = JOBS.get(job_id)
                if current and current.get("status") not in {"done", "error"}:
                    current.update(
                        status="error",
                        error="Processing stopped unexpectedly. Please retry the upload.",
                        finished_at=time.time(),
                    )
                job = dict(JOBS.get(job_id) or job)
        snap = {k: job.get(k) for k in ("status", "stage", "step", "total", "lecture_id", "error", "warnings")}
        if snap != last:
            yield json.dumps(snap) + "\n"
            last, last_beat = snap, time.time()
        elif time.time() - last_beat > 10:
            yield "\n"  # heartbeat so proxies keep the connection open
            last_beat = time.time()
        if job.get("status") in ("done", "error"):
            break
        time.sleep(1)


# ── Routes: health + processing ──────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=256)
    role: Literal["student", "farmer"] = "student"


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=256)


@app.post("/api/auth/register")
def register(req: RegisterRequest, response: Response, request: Request):
    client = request.client.host if request.client else "unknown"
    if not allow_auth_attempt(client):
        raise HTTPException(429, "Too many authentication attempts. Try again in a few minutes.")
    try:
        user = auth_store.create_user(req.email, req.display_name, req.password, req.role)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    token, csrf_token = auth_store.create_session(user["id"])
    set_session_cookie(response, token)
    return {"user": user, "csrf_token": csrf_token}


@app.post("/api/auth/login")
def login(req: LoginRequest, response: Response, request: Request):
    client = request.client.host if request.client else "unknown"
    if not allow_auth_attempt(client):
        raise HTTPException(429, "Too many login attempts. Try again in a few minutes.")
    user = auth_store.authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(401, "Email or password is incorrect, or the account is disabled.")
    clear_auth_attempts(client)
    token, csrf_token = auth_store.create_session(user["id"])
    set_session_cookie(response, token)
    return {"user": user, "csrf_token": csrf_token}


@app.get("/api/auth/me")
def me(request: Request, user: dict = Depends(current_user)):
    session = auth_store.get_session(request.cookies.get(SESSION_COOKIE))
    return {"user": user, "csrf_token": session["csrf_token"]}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response, user: dict = Depends(current_user)):
    auth_store.revoke_session(request.cookies.get(SESSION_COOKIE))
    clear_session_cookie(response)
    return {"logged_out": True}


@app.get("/api/admin/users")
def admin_users(user: dict = Depends(ADMIN_ONLY)):
    return auth_store.list_users()


class ActiveUserRequest(BaseModel):
    is_active: bool


@app.patch("/api/admin/users/{user_id}/active")
def change_user_active(user_id: int, req: ActiveUserRequest, user: dict = Depends(ADMIN_ONLY)):
    if user_id == user["id"] and not req.is_active:
        raise HTTPException(400, "You cannot disable your own active administrator account.")
    if not auth_store.set_user_active(user_id, req.is_active):
        raise HTTPException(404, "User not found")
    return {"user_id": user_id, "is_active": req.is_active}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "max_upload_mb": MAX_UPLOAD_MB,
        "youtube_enabled": YOUTUBE_ENABLED,
        "youtube_captions_enabled": True,
        "max_reference_file_mb": MAX_REFERENCE_FILE_MB,
        "max_reference_files": MAX_REFERENCE_FILES,
        "reference_extensions": sorted(REFERENCE_EXTENSIONS),
        "max_document_file_mb": MAX_DOCUMENT_FILE_MB,
        "max_document_files": MAX_DOCUMENT_FILES,
        "document_extensions": sorted(REFERENCE_EXTENSIONS),
    }


def _save_reference_uploads(
    uploads: list[UploadFile],
    remaining_bytes: int | None = None,
    max_files: int = MAX_REFERENCE_FILES,
    max_file_mb: int = MAX_REFERENCE_FILE_MB,
    file_label: str = "lecturer",
) -> list[dict]:
    named_uploads = [item for item in uploads if item and (item.filename or "").strip()]
    if len(named_uploads) > max_files:
        raise HTTPException(400, f"Upload at most {max_files} {file_label} files.")

    paths: list[dict] = []
    max_file_bytes = max_file_mb * 1024 * 1024
    budget = MAX_UPLOAD_MB * 1024 * 1024 if remaining_bytes is None else remaining_bytes
    total_bytes = 0
    try:
        for upload_file in named_uploads:
            supplied_name = (upload_file.filename or "document").replace("\\", "/")
            original_name = os.path.basename(supplied_name) or "document"
            ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
            if ext not in REFERENCE_EXTENSIONS:
                accepted = ", ".join(sorted(REFERENCE_EXTENSIONS))
                raise HTTPException(400, f"Unsupported {file_label} document '{original_name}'. Use: {accepted}.")

            path = None
            size = 0
            with tempfile.NamedTemporaryFile(delete=False, suffix="." + ext, prefix="lecturer_material_") as tmp:
                path = tmp.name
                while True:
                    chunk = upload_file.file.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    total_bytes += len(chunk)
                    if size > max_file_bytes:
                        raise HTTPException(413, f"'{original_name}' is larger than {max_file_mb} MB.")
                    if total_bytes > budget:
                        raise HTTPException(413, f"The combined upload exceeds {MAX_UPLOAD_MB} MB. Reduce the selected files.")
                    tmp.write(chunk)

            if size == 0:
                os.remove(path)
                raise HTTPException(400, f"'{original_name}' is empty.")
            paths.append({"path": path, "filename": original_name})
        return paths
    except Exception:
        for item in paths:
            try:
                os.remove(item["path"])
            except OSError:
                pass
        if 'path' in locals() and path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
        raise


def extract_reference_text(path: str, filename: str) -> str:
    """Compatibility wrapper for document extraction used by lecture uploads."""
    from utils.document_reader import read_document_text
    return read_document_text(path, filename)


@app.post("/api/lectures/upload")
def upload(file: UploadFile = File(...), reference_files: list[UploadFile] = File(default=[]), user: dict = Depends(STUDENT_OR_ADMIN)):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Unsupported file type. Use: " + ", ".join(sorted(ALLOWED_EXTENSIONS)))
    size, limit = 0, MAX_UPLOAD_MB * 1024 * 1024
    with tempfile.NamedTemporaryFile(delete=False, suffix="." + ext) as tmp:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                tmp.close()
                os.remove(tmp.name)
                raise HTTPException(413, f"File is larger than {MAX_UPLOAD_MB} MB.")
            tmp.write(chunk)
        path = tmp.name
    if size == 0:
        os.remove(path)
        raise HTTPException(400, "This file is empty.")
    try:
        notes = _save_reference_uploads(reference_files, remaining_bytes=limit - size)
    except Exception:
        try:
            os.remove(path)
        except OSError:
            pass
        raise
    job_id, thread = start_job(
        path, False, user["id"], notes,
        display_title=uploaded_lecture_title(file.filename),
    )
    return StreamingResponse(job_events(job_id, thread), media_type="application/x-ndjson")


@app.post("/api/lectures/documents")
def upload_documents(
    files: list[UploadFile] = File(default=[]),
    user: dict = Depends(STUDENT_OR_ADMIN),
):
    """Create a study workspace from PDF, DOCX, PPTX, TXT or Markdown files."""
    if not files:
        raise HTTPException(400, "Choose at least one document to upload.")
    saved_files = _save_reference_uploads(
        files,
        max_files=MAX_DOCUMENT_FILES,
        max_file_mb=MAX_DOCUMENT_FILE_MB,
        file_label="document",
    )
    if not saved_files:
        raise HTTPException(400, "Choose at least one supported document.")
    job_id, thread = start_document_job(saved_files, user["id"])
    return StreamingResponse(job_events(job_id, thread), media_type="application/x-ndjson")


class YouTubeRequest(BaseModel):
    url: str


@app.post("/api/lectures/youtube")
async def from_youtube(request: Request, user: dict = Depends(STUDENT_OR_ADMIN)):
    # Keep support for existing JSON clients while accepting multipart form data
    # from the frontend when lecturer documents are attached.
    content_type = request.headers.get("content-type", "").lower()
    if "multipart/form-data" in content_type:
        form = await request.form()
        url = str(form.get("url", "")).strip()
        reference_uploads = form.getlist("reference_files")
    else:
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(400, "Provide a YouTube URL.")
        url = str(payload.get("url", "")).strip() if isinstance(payload, dict) else ""
        reference_uploads = []

    if not valid_youtube_url(url):
        raise HTTPException(400, "Please provide a link to a single YouTube video.")
    notes = _save_reference_uploads(reference_uploads)
    job_id, thread = start_job(url, True, user["id"], notes)
    return StreamingResponse(job_events(job_id, thread), media_type="application/x-ndjson")


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str, user: dict = Depends(STUDENT_OR_ADMIN)):
    with JOB_LOCK:
        job = dict(JOBS.get(job_id) or {})
    if not job or (user["role"] != "admin" and job.get("owner_user_id") != user["id"]):
        raise HTTPException(404, "Job not found")
    return {k: v for k, v in job.items() if k not in {"owner_user_id", "created_at", "finished_at"}}


# ── Routes: library (My Lectures) ────────────────────────────────────────────
@app.get("/api/lectures")
def lectures(user: dict = Depends(STUDENT_OR_ADMIN)):
    from core.vector_store import list_lectures
    items = list_lectures()
    if user["role"] != "admin":
        items = [l for l in items if lecture_belongs_to_user(l, user)]
    return [with_title(l) for l in items]


class RenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


@app.patch("/api/lectures/{lecture_id}")
def rename(lecture_id: str, req: RenameRequest, user: dict = Depends(STUDENT_OR_ADMIN)):
    require_lecture_access(lecture_id, user)
    with TITLE_LOCK:
        titles = load_titles()
        titles[lecture_id] = req.title.strip()
        save_titles(titles)
    return {"id": lecture_id, "title": req.title.strip()}


@app.delete("/api/lectures/{lecture_id}")
def remove(lecture_id: str, user: dict = Depends(STUDENT_OR_ADMIN)):
    from core.vector_store import delete_lecture
    require_lecture_access(lecture_id, user)
    delete_lecture(lecture_id)
    with TITLE_LOCK:
        titles = load_titles()
        if titles.pop(lecture_id, None) is not None:
            save_titles(titles)
    RUNTIME.pop(lecture_id, None)
    SUMMARIES.pop(lecture_id, None)
    DETAILED_NOTES.pop(lecture_id, None)
    with ENGINE_LOCK:
        for key in [k for k in ENGINES if k[0] == lecture_id]:
            ENGINES.pop(key, None)
    return {"deleted": lecture_id}


# ── Routes: workspace (chat, summary, quiz, evaluation) ──────────────────────
SESSION_ID_PATTERN = r"^[A-Za-z0-9._:-]+$"


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(default="default", min_length=1, max_length=64)
    response_language: Literal["auto", "English", "Hindi", "Hinglish"] = "auto"
    response_style: Literal["balanced", "simple", "exam", "step_by_step"] = "balanced"
    response_length: Literal["concise", "standard", "detailed"] = "standard"

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question cannot be empty or whitespace only.")
        return value

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(SESSION_ID_PATTERN, value):
            raise ValueError("Session ID may contain only letters, numbers, dots, underscores, colons, and hyphens.")
        return value


def source_payload(docs) -> list[dict]:
    """Serialize retrieved passages with their original source locations."""
    payload = []
    for doc in docs:
        metadata = doc.metadata or {}
        text = doc.page_content
        filename = metadata.get("filename") or metadata.get("source")
        if filename == "unknown":
            filename = None

        # Read legacy location markers too, so older Chroma collections remain
        # useful until the user reprocesses them with the updated chunker.
        page_number = metadata.get("page_number")
        if page_number is None:
            page_match = re.search(r"(?m)^\s*\[Page\s+(\d+)\]", text)
            page_number = int(page_match.group(1)) if page_match else None

        slide_number = metadata.get("slide_number")
        if slide_number is None:
            slide_match = re.search(r"(?m)^\s*\[Slide\s+(\d+)\]", text)
            slide_number = int(slide_match.group(1)) if slide_match else None

        timestamp = metadata.get("start_time_str")
        if timestamp is None:
            time_match = re.search(r"\[(?:(\d{1,3}):)?([0-5]?\d):([0-5]\d)\]", text)
            timestamp = time_match.group(0)[1:-1] if time_match else None

        payload.append({
            "text": text,
            "time": timestamp,
            "source": (metadata.get("source") if metadata.get("source") != "unknown" else None) or filename,
            "filename": filename,
            "source_type": metadata.get("source_type"),
            "page_number": page_number,
            "slide_number": slide_number,
            "chunk_id": metadata.get("document_chunk", metadata.get("chunk_id")),
        })
    return payload


@app.post("/api/lectures/{lecture_id}/chat")
def chat(lecture_id: str, req: ChatRequest, user: dict = Depends(STUDENT_OR_ADMIN)):
    """Streams newline-delimited JSON: one 'sources' line, many 'token' lines, then 'done'."""
    require_lecture_access(lecture_id, user)
    enforce_model_request_limit(user["id"])
    engine = get_engine(lecture_id, req.session_id, user["id"])
    try:
        stream, sources, save = engine.prepare_stream(
            req.question.strip(),
            preferences={
                "response_language": req.response_language,
                "response_style": req.response_style,
                "response_length": req.response_length,
            },
        )
    except Exception as e:
        raise HTTPException(500, friendly_error(e))

    def events():
        yield json.dumps({"type": "sources", "data": source_payload(sources)}) + "\n"
        parts = []
        try:
            for token in stream:
                parts.append(token)
                yield json.dumps({"type": "token", "data": token}) + "\n"
            save("".join(parts))
            yield json.dumps({"type": "done"}) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "data": friendly_error(e)}) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson")


@app.post("/api/lectures/{lecture_id}/chat/reset")
def reset_chat(
    lecture_id: str,
    session_id: str = Query(default="default", min_length=1, max_length=64, pattern=SESSION_ID_PATTERN),
    user: dict = Depends(STUDENT_OR_ADMIN),
):
    require_lecture_access(lecture_id, user)
    key = (str(lecture_id), int(user["id"]), session_id.strip())
    with ENGINE_LOCK:
        ENGINES.pop(key, None)
    return {"reset": True}


@app.get("/api/lectures/{lecture_id}/summary")
def summary(lecture_id: str, refresh: bool = False, user: dict = Depends(STUDENT_OR_ADMIN)):
    require_lecture_access(lecture_id, user)
    if refresh or lecture_id not in SUMMARIES:
        enforce_model_request_limit(user["id"])
        from features.summarizer import summarize
        docs = get_runtime(lecture_id)["docs"]
        try:
            SUMMARIES[lecture_id] = summarize(docs)
        except Exception as e:
            raise HTTPException(500, friendly_error(e))
    return {"summary": SUMMARIES[lecture_id]}


@app.get("/api/lectures/{lecture_id}/detailed-notes")
def detailed_notes(lecture_id: str, refresh: bool = False, user: dict = Depends(STUDENT_OR_ADMIN)):
    require_lecture_access(lecture_id, user)
    if refresh or lecture_id not in DETAILED_NOTES:
        enforce_model_request_limit(user["id"])
        from features.detailed_notes import generate_detailed_notes
        docs = get_runtime(lecture_id)["docs"]
        try:
            DETAILED_NOTES[lecture_id] = generate_detailed_notes(docs)
        except Exception as e:
            raise HTTPException(500, friendly_error(e))
    return {"detailed_notes": DETAILED_NOTES[lecture_id]}


class QuizRequest(BaseModel):
    num_questions: int = Field(default=5, ge=1, le=10)


@app.post("/api/lectures/{lecture_id}/quiz")
def quiz(lecture_id: str, req: QuizRequest, user: dict = Depends(STUDENT_OR_ADMIN)):
    require_lecture_access(lecture_id, user)
    enforce_model_request_limit(user["id"])
    from features.quiz_generator import generate_quiz
    docs = get_runtime(lecture_id)["docs"]
    try:
        questions = generate_quiz(docs, num_questions=req.num_questions)
    except Exception as e:
        raise HTTPException(500, friendly_error(e))
    if not questions:
        raise HTTPException(502, "The quiz couldn't be generated this time. Please try again.")
    return {"questions": questions}


class EvalItem(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    ground_truth: str = Field(min_length=1, max_length=5000)

    @field_validator("question", "ground_truth")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty or whitespace only.")
        return value


class EvalRequest(BaseModel):
    items: list[EvalItem] = Field(min_length=1, max_length=20)


@app.post("/api/lectures/{lecture_id}/evaluate")
def evaluate(lecture_id: str, req: EvalRequest, user: dict = Depends(ADMIN_ONLY)):
    require_lecture_access(lecture_id, user)
    enforce_model_request_limit(user["id"])
    from features.evaluator import quick_evaluate
    eval_session_id = "eval-" + uuid.uuid4().hex[:8]
    engine = get_engine(lecture_id, eval_session_id, user["id"])  # fresh, user-scoped memory
    items = [i.model_dump() for i in req.items if i.question.strip() and i.ground_truth.strip()]
    if not items:
        raise HTTPException(400, "Each test row needs both a question and an expected answer.")
    try:
        scores = quick_evaluate(engine, items)
    except Exception as e:
        raise HTTPException(500, f"Evaluation failed. {friendly_error(e)}")
    finally:
        with ENGINE_LOCK:
            ENGINES.pop((str(lecture_id), int(user["id"]), eval_session_id), None)
    return {"scores": scores, "n": len(items)}


class FarmCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    location: str = Field(default="", max_length=200)
    crop: str = Field(default="", max_length=120)
    soil_moisture: float | None = Field(default=None, ge=0, le=100)
    temperature_c: float | None = Field(default=None, ge=-50, le=80)
    humidity_pct: float | None = Field(default=None, ge=0, le=100)
    notes: str = Field(default="", max_length=5000)


class FarmUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=200)
    crop: str | None = Field(default=None, max_length=120)
    soil_moisture: float | None = Field(default=None, ge=0, le=100)
    temperature_c: float | None = Field(default=None, ge=-50, le=80)
    humidity_pct: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=5000)


@app.get("/api/farms")
def farms(user: dict = Depends(FARMER_ONLY)):
    return auth_store.list_farms(user["id"])


@app.post("/api/farms")
def create_farm(req: FarmCreateRequest, user: dict = Depends(FARMER_ONLY)):
    data = req.model_dump()
    data["name"] = data["name"].strip()
    if not data["name"]:
        raise HTTPException(400, "Farm name cannot be empty.")
    return auth_store.create_farm(user["id"], data)


@app.get("/api/farms/{farm_id}")
def farm_detail(farm_id: str, user: dict = Depends(FARMER_ONLY)):
    farm = auth_store.get_farm(farm_id)
    if not farm or farm["owner_user_id"] != user["id"]:
        raise HTTPException(404, "Farm not found")
    return farm


@app.patch("/api/farms/{farm_id}")
def edit_farm(farm_id: str, req: FarmUpdateRequest, user: dict = Depends(FARMER_ONLY)):
    current = auth_store.get_farm(farm_id)
    if not current or current["owner_user_id"] != user["id"]:
        raise HTTPException(404, "Farm not found")
    updated = auth_store.update_farm(farm_id, user["id"], req.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(404, "Farm not found")
    return updated


@app.delete("/api/farms/{farm_id}")
def remove_farm(farm_id: str, user: dict = Depends(FARMER_ONLY)):
    farm = auth_store.get_farm(farm_id)
    if not farm or farm["owner_user_id"] != user["id"]:
        raise HTTPException(404, "Farm not found")
    if not auth_store.delete_farm(farm_id, user["id"]):
        raise HTTPException(404, "Farm not found")
    return {"deleted": farm_id}


# ── Optional: serve the frontend from the same server (one deployment, no CORS) ─
if os.path.isdir("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")