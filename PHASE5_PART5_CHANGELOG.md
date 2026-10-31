# Phase 5 — Part 5: Frontend and User Experience

## Changes

- Added drag-and-drop support for audio/video uploads, standalone document uploads, and optional lecturer reference files. Existing file pickers remain available.
- Reuses the existing file-selection handlers after a drop, preserving extension, file-count, and size validation.
- Added explicit handling for browsers without the `DataTransfer` API.
- Added accessible upload progress semantics (`role="progressbar"`, `aria-valuenow`, live processing status, and `aria-busy`).
- Added a question character counter to the chat composer.
- Added copy-passage actions to each retrieved source card.
- Added source chunk identifiers to the displayed provenance when available.
- Improved workspace tab semantics and keyboard navigation (Left/Right, Home, End).
- Added visible keyboard-focus and drag-over styles, with reduced-motion support.

## Compatibility

- No backend routes or request payloads changed.
- The existing NDJSON upload and chat streaming formats remain unchanged.
- Existing file-picker workflows and API-side validation remain in place.
- The existing layout, theme preferences, and study features are retained.

## Verification

- `node --check frontend/script.js` passed.
- `python -m unittest tests.test_frontend_ux` passed (8 frontend source-contract tests).
- The complete project test suite was attempted in the build container. Six existing test modules could not import because the container does not have `langchain_text_splitters`, `langchain_core`, and `langchain_groq`. The user's Windows virtual environment previously passed all 81 pre-Part-5 tests; run the complete suite there after applying this patch.

## Manual browser checks

1. Drag one supported audio/video file onto the lecture upload area.
2. Drag several supported PDF/DOCX/PPTX/TXT/MD files onto the document upload card.
3. Drag lecturer reference files onto the optional lecturer-notes card.
4. Confirm unsupported extensions, file count limits, and size limits are still rejected.
5. Start processing and confirm the progress text and bar update.
6. Open chat, type a question, and verify the character count resets after sending.
7. Expand an answer's source panel and use **Copy passage**.
8. Navigate workspace tabs using Left/Right arrows and Home/End.
9. Check the upload and chat layouts at mobile width and in dark mode.
