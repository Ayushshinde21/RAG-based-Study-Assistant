# Campus Study Desk updates

## Lecturer material during lecture upload

When uploading an audio/video recording or processing a YouTube lecture, the dashboard now offers an optional lecturer-material upload. Supported formats are PDF, DOCX, PPTX, TXT, and Markdown (`.md`). Up to five files can be attached, with a default limit of 15 MB per file. The combined request must remain within `MAX_UPLOAD_MB`.

The backend extracts the document text and indexes it in the same lecture collection as the transcript. Chat retrieval, summaries, and detailed notes can therefore use both sources. Unreadable optional files are reported as warnings and do not cancel an otherwise successful recording import. Scanned PDFs without selectable text may still require OCR before uploading.

## Detailed Notes workspace tab

A new **Detailed Notes** tab sits beside **Summary**. It generates an expanded, Markdown-formatted study guide with explanations, definitions, examples where supported, revision checkpoints, and self-check questions. The view includes section navigation, refresh/retry, copy, Markdown download, and an option to discuss the notes with the chat assistant.

## Install requirements

Install/update project packages after pulling these changes:

```bash
pip install -r requirements.txt
```

The new supported office formats use `python-docx` and `python-pptx`; PDF extraction uses the existing `pypdf` dependency.
