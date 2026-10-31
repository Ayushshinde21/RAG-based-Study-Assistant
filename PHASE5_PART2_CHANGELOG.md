# Phase 5 — Part 2: Document Ingestion

## What changed

- Added `utils/document_reader.py` as a shared extraction and text-normalization layer for PDF, DOCX, PPTX, TXT and Markdown.
- Preserved PDF page markers and PowerPoint slide markers so the existing chunker can attach page/slide metadata to chunks.
- Preserved Markdown headings, lists, code fences and meaningful line breaks during text cleanup.
- Kept `api.extract_reference_text()` as a compatibility wrapper, so lecturer notes attached to an audio/video lecture continue to use the shared reader.
- Added authenticated endpoint `POST /api/lectures/documents` for creating a study workspace directly from one or more documents, without requiring an audio/video upload.
- Added a dashboard flow labelled **Start with documents**. It accepts up to the configured number of PDF, DOCX, PPTX, TXT or Markdown files and streams processing progress like the existing lecture upload flow.
- Added document-only processing: extract, normalize, chunk, attach metadata, build ChromaDB and BM25 retrievers, and register the workspace in the lecture library.
- Added `content_type` and `source_files` fields to new lecture registry records. Existing `register_lecture()` calls remain compatible because both parameters have defaults.
- Added environment settings to `.env.example`:
  - `MAX_DOCUMENT_FILES=5`
  - `MAX_DOCUMENT_FILE_MB=15`
  - `MAX_DOCUMENT_TEXT_CHARS=250000`
- Added regression tests for document extraction, upload authorization, the upload route, successful indexing, and temporary-file cleanup.

## Metadata attached to document chunks

Standalone document chunks now carry:

- `source_type`: `uploaded_document`
- `filename`
- `document_type`
- `document_id`
- `document_chunk`
- `ingestion_batch_id`
- Existing `page_number` or `slide_number`, when extracted from the source

## Current limits

- Supported formats: PDF, DOCX, PPTX, TXT and Markdown.
- Scanned/image-only PDFs are detected and reported; OCR is not included in this part.
- DOCX extraction reads paragraphs and tables. PPTX extraction reads slide text and tables. Embedded images, diagrams and chart images are not OCR-processed.
- Text above `MAX_DOCUMENT_TEXT_CHARS` is truncated with a visible processing warning.
- Documents are indexed into one study workspace per upload batch. Each chunk retains its originating filename and available page/slide location.

## Verification performed in the build environment

- 11 document-reader tests passed.
- 3 document-upload route tests passed.
- 2 standalone document-job tests passed.
- 2 source-integrity tests passed.
- Python compilation passed for the changed Python files.
- `node --check frontend/script.js` passed.

The complete project test suite still needs to be run in the user's project virtual environment because the build environment does not include the project's LangChain/Chroma dependencies.

## Apply

Extract the patch ZIP into the existing `RAG based Study Assistant` project root and allow the listed files to be replaced. Then run:

```powershell
python run_tests.py
```
