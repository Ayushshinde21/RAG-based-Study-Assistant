---
title: Campus Study Desk
colorFrom: green
colorTo: blue
sdk: docker
app_port: 8080
pinned: false
---

# Campus Study Desk

Campus Study Desk is a lecture-based study assistant. It can transcribe supported recordings, index lecture passages, answer questions using retrieved material, prepare summaries and detailed notes, generate quizzes, and evaluate answers. Outputs can be incomplete or wrong, so check them against the original lecture and the source passages shown by the app.

## Application interfaces

- `frontend/` contains the browser interface with the dashboard, lecture library, study workspace, privacy policy, and terms and conditions pages.
- `api.py` provides the FastAPI endpoints and can serve the browser interface from the same process.
- `app.py` is a legacy Streamlit interface. Do not deploy it publicly for this app: it does not use the new account and ownership checks. The included Docker deployment starts the protected FastAPI website instead.

## Run the FastAPI interface locally

1. Install a supported Python version and FFmpeg.
2. Create a virtual environment and install `requirements.txt`.
3. Copy `.env.example` to `.env` and fill in the keys for the features you enable. Keep `.env` out of Git.
4. From the repository root, run `uvicorn api:app --reload --port 8000`.
5. Open `http://127.0.0.1:8000`.

Read `AUTH_AND_DATA_ACCESS.md` and `LAUNCH_CHECKLIST.md` before deployment. In particular, the current API does not provide built-in user authentication or per-user data isolation. Do not expose it publicly with real student materials until access controls and data handling have been reviewed and tested. Fill in the operator-specific legal details before launching.

## Account security and farmer data

See [`AUTH_AND_DATA_ACCESS.md`](AUTH_AND_DATA_ACCESS.md) for account setup, role permissions, local run instructions, and production limitations. Student lecture ownership and farmer farm-record ownership are checked by the API. Configure `ADMIN_EMAIL` and `ADMIN_PASSWORD` in an untracked `.env` before starting the server to bootstrap the administrator.
