# Phase 5, Part 1 — Source Metadata and Citation Provenance

## What changed

- Fixed-size chunking now recognizes `[Page N]` and `[Slide N]` markers and stores the location as structured `page_number` or `slide_number` metadata.
- Fixed-size and semantic chunks now retain the source filename and document chunk index in metadata.
- Timestamped transcript chunks now retain the first timestamp in `start_time_str`, including short transcripts that use fixed chunking.
- RAG prompt context labels now include the source filename and page/slide/timestamp when those fields are available.
- The chat API now returns filename, source type, page, slide, timestamp, and chunk ID alongside each source passage.
- The frontend source panel now displays the filename and page/slide location, plus timestamps when available.
- The API has a fallback that reads legacy `[Page N]`, `[Slide N]`, and timestamp markers from older stored chunks.
- RRF now distinguishes identical text passages from different source locations, rather than merging them and potentially losing provenance.

## Files changed

- `core/chunker.py`
- `core/rag_engine.py`
- `core/hybrid_retriever.py`
- `api.py`
- `frontend/script.js`
- `frontend/style.css`
- `tests/test_rag_prompt.py`
- `tests/test_hybrid_retriever.py`
- `tests/test_source_metadata.py` (new)

## Important note about existing indexes

Existing Chroma collections are not rewritten automatically. The API can recover old page, slide, and timestamp markers when they remain in stored chunk text. To get the new structured page/slide metadata on newly processed documents, reprocess those lecturer reference files after installing this update.

## Verification performed in this environment

- Python syntax compilation: passed for all modified Python modules and tests.
- JavaScript syntax check (`node --check frontend/script.js`): passed.
- Manual metadata checks with lightweight dependency stubs: passed for page markers, slide markers, transcript timestamps, source payload serialization, prompt provenance labels, and RRF identity handling.
- The full project test suite could not be run here because the container does not have the project's LangChain dependencies installed and package installation is unavailable. Run `python run_tests.py` in the project's existing `.venv` to complete regression verification.
