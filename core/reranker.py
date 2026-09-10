from sentence_transformers import CrossEncoder
from langchain_core.documents import Document

# Load CrossEncoder model once
model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank(query: str, docs: list[Document], top_n: int = 5) -> list[Document]:
    """
    Rerank documents using CrossEncoder.
    CrossEncoder scores each query-document pair directly
    which is more accurate than vector similarity alone.
    Returns top_n most relevant documents.
    """
    if not docs:
        return []

    # create query-document pairs
    pairs = [(query, doc.page_content) for doc in docs]

    # score all pairs
    scores = model.predict(pairs)

    # sort by score descending
    scored_docs = sorted(
        zip(scores, docs),
        key=lambda x: x[0],
        reverse=True
    )

    # return top_n docs
    top_docs = [doc for _, doc in scored_docs[:top_n]]

    print(f"🎯 Reranked {len(docs)} → top {len(top_docs)} chunks")
    return top_docs
