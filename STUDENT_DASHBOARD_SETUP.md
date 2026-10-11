# Campus Study Desk — Student Dashboard Update

## What changed

- Rebuilt the HTML/JavaScript frontend dashboard for a student-first learning experience.
- Added live metrics sourced from the lecture API: saved lectures and indexed chunks.
- Added continue-learning, learning-tool shortcuts, recent lectures, study tips, and API connection state.
- Kept lecture upload/processing, optional YouTube ingestion, the searchable lecture library, dark mode, and the existing Chat/Summary/Quiz/Evaluation workspace.
- Polished AI chat with formatted headings, bullets, inline code and code blocks, suggested prompts, streaming feedback, copy-answer actions, and expandable lecture source passages.
- Rebuilt summaries as readable study notes with nested bullet styling, section navigation, reading-time/word-count metadata, copy and refresh actions, and a shortcut to discuss the notes with AI.
- Expanded the workspace canvas while a lecture is open and refined tablet/mobile layouts.

## Run the updated frontend

1. Preserve your original `.env` file and its API keys. The update archive intentionally does not include secrets. If setting up a fresh copy, copy `.env.example` to `.env` and fill in the values required by your environment.
2. Open a terminal in this project folder and activate your virtual environment.
3. Install dependencies if needed: `pip install -r requirements.txt`.
4. Start the frontend and API together: `uvicorn api:app --reload --port 8000`.
5. Open `http://127.0.0.1:8000`.

The Dockerfile also runs `api:app` and serves the files in `frontend/`. The separate Streamlit entry point (`app.py`) is unchanged; use `uvicorn api:app` to see the new HTML dashboard.
