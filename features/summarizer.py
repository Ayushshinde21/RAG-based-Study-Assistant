from core.llm import get_gemini_llm, response_text
from langchain_core.documents import Document


def get_llm(*, response_mime_type: str | None = None):
    return get_gemini_llm(response_mime_type=response_mime_type)


def select_context_docs(docs: list[Document], max_chunks: int = 15) -> list[Document]:
    """Select spread-out transcript chunks and include lecturer material when available."""
    transcript_docs = [d for d in docs if d.metadata.get("source_type") != "lecturer_material"]
    lecturer_docs = [d for d in docs if d.metadata.get("source_type") == "lecturer_material"]

    def spread(items, count):
        if count <= 0 or not items:
            return []
        if count >= len(items):
            return list(items)
        if count == 1:
            return [items[len(items) // 2]]
        indices = [round(i * (len(items) - 1) / (count - 1)) for i in range(count)]
        return [items[i] for i in indices]

    target_total = min(max_chunks, len(docs))
    if not lecturer_docs:
        return spread(transcript_docs, target_total)
    if not transcript_docs:
        return spread(lecturer_docs, target_total)

    lecturer_target = min(len(lecturer_docs), max(1, target_total // 3))
    transcript_target = min(len(transcript_docs), target_total - lecturer_target)
    while transcript_target + lecturer_target < target_total:
        if transcript_target < len(transcript_docs):
            transcript_target += 1
        elif lecturer_target < len(lecturer_docs):
            lecturer_target += 1
        else:
            break
    selected_transcript = spread(transcript_docs, transcript_target)
    selected_lecturer = spread(lecturer_docs, lecturer_target)

    # Interleave the two sources so a long transcript cannot push lecturer
    # material out of the prompt's character budget.
    selected = []
    for index in range(max(len(selected_transcript), len(selected_lecturer))):
        if index < len(selected_transcript):
            selected.append(selected_transcript[index])
        if index < len(selected_lecturer):
            selected.append(selected_lecturer[index])
    return selected


def build_context_text(docs: list[Document], max_chunks: int = 15,
                       max_chars: int = 12000) -> str:
    selected = select_context_docs(docs, max_chunks=max_chunks)
    parts = []
    for doc in selected:
        is_lecturer_material = doc.metadata.get("source_type") == "lecturer_material"
        source_name = doc.metadata.get("filename") or doc.metadata.get("source") or "lecture material"
        kind = "LECTURER MATERIAL" if is_lecturer_material else "LECTURE TRANSCRIPT"
        parts.append(f"[{kind} · {source_name}]\n{doc.page_content}")
    return "\n\n".join(parts)[:max_chars]


def summarize(docs: list[Document], max_chunks: int = 15) -> str:
    """
    Summarize lecture content from a list of Document chunks.
    Limits chunks to avoid exceeding token limits.
    """
    if not docs:
        raise ValueError("No documents to summarize")

    # Use representative passages from across the lecture and include uploaded
    # lecturer notes instead of silently ignoring notes placed after the transcript.
    full_text = build_context_text(docs, max_chunks=max_chunks, max_chars=12000)

    prompt = f"""You are an expert study assistant.
Summarize the following lecture transcript and lecturer-provided material into clear, concise revision notes.
Cover the main topics, definitions, key concepts, and important distinctions.
Use a clear heading hierarchy and concise bullet points. Preserve equations, examples, or code when present.
Do not invent facts that are not supported by the material. If sources appear to conflict, explicitly note the conflict.

--- LECTURE CONTENT ---
{full_text}

--- SUMMARY ---"""

    llm = get_llm()
    response = llm.invoke(prompt)
    summary = response_text(response)
    if not summary:
        raise RuntimeError("Gemini returned an empty summary. Please try again.")

    print(f"✅ Summary generated! ({len(summary)} characters)")
    return summary


def summarize_from_text(text: str) -> str:
    """
    Summarize from raw text string directly.
    """
    from langchain_core.documents import Document
    doc = Document(page_content=text)
    return summarize([doc])
