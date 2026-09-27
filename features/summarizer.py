import os
from langchain_groq import ChatGroq
from langchain_core.documents import Document


def get_llm():
    return ChatGroq(
        model="groq/compound",  # replace with your working model
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.3,
    )


def summarize(docs: list[Document], max_chunks: int = 15) -> str:
    """
    Summarize lecture content from a list of Document chunks.
    Limits chunks to avoid exceeding token limits.
    """
    if not docs:
        raise ValueError("No documents to summarize")

    # limit chunks to avoid TPM overflow
    docs_to_use = docs[:max_chunks] if len(docs) > max_chunks else docs

    full_text = "\n\n".join([doc.page_content for doc in docs_to_use])

    # also truncate total characters as safety net
    max_chars = 12000
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars]

    prompt = f"""You are an AI study assistant. 
Summarize the following lecture content into clear, concise bullet points.
Cover all the main topics and key concepts.
Format: use bullet points starting with •

--- LECTURE CONTENT ---
{full_text}

--- SUMMARY ---"""

    llm = get_llm()
    response = llm.invoke(prompt)
    summary = response.content.strip()

    print(f"✅ Summary generated! ({len(summary)} characters)")
    return summary


def summarize_from_text(text: str) -> str:
    """
    Summarize from raw text string directly.
    """
    from langchain_core.documents import Document
    doc = Document(page_content=text)
    return summarize([doc])
