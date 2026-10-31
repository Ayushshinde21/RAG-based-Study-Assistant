# Phase 5 — Part 3: Audio and Video Ingestion Reliability

## What changed

- Added `utils/http_retry.py` for bounded retries on network timeouts, connection errors, HTTP 408/429, and transient 5xx responses.
- The retry helper uses finite connect/read timeouts, exponential backoff, and respects numeric or HTTP-date `Retry-After` values within a bounded wait.
- Applied bounded HTTP retries and finite timeouts to Sarvam speech-to-text and Hindi-to-English translation requests.
- Made Sarvam parallel request concurrency configurable through `SARVAM_MAX_WORKERS` (default 3, bounded to 8) to reduce provider overload on long Hindi lectures.
- Added a local faster-whisper translation path for detected non-English languages, including Hindi when `SARVAM_API_KEY` is not configured. English audio continues to use transcription rather than translation.
- Passed the detected language and Whisper task through long-audio chunk processing, preserving absolute timestamps in translated segments.
- Improved FFmpeg chunk-preparation errors so missing FFmpeg and failed segments produce actionable messages.
- Validated ffprobe duration output against non-finite and negative values.
- Preserved the user's original uploaded audio/video filename as the lecture title instead of exposing the generated temporary filename.
- Added regression tests for retry behavior, provider concurrency settings, language routing, translation-task propagation, FFmpeg error handling, and upload-title preservation.

## Existing functionality retained

- Audio extraction from uploaded video files.
- Direct audio uploads and format conversion.
- YouTube caption-first processing and audio fallback.
- Whisper English transcription with timestamps.
- Sarvam Hindi transcription and translation when `SARVAM_API_KEY` is configured.
- Long-recording segmentation and absolute timestamp offsets.
- Transcript chunking and indexing into the existing RAG pipeline.

## Configuration

Add or retain this in `.env` when tuning Sarvam parallelism:

```env
SARVAM_MAX_WORKERS=3
```

The default is intentionally conservative. Increase it only if the provider quota and local resources support more concurrent requests.

## Verification performed in the build environment

- 22 focused tests passed across HTTP retries, transcription routing, translator chunking, and long-video processing.
- Python compilation passed for changed Python files.
- The complete project test suite was not run in this build environment because the project dependencies `langchain_core`, `chromadb`, and `faster_whisper` are not installed here. Run `python run_tests.py` in the project's `.venv` after applying the patch.
- No live Sarvam, Groq, or YouTube requests were made during testing.

## Apply

Extract the patch ZIP into the existing `RAG based Study Assistant` project root and allow the listed files to be replaced. Then run:

```powershell
python run_tests.py
```
