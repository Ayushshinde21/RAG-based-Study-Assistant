from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever


def build_bm25_retriever(docs: list[Document], k: int = 10) -> BM25Retriever:
    """
    Build BM25 keyword retriever from documents.
    BM25 is good at exact keyword matching.
    Returns top-k results.
    """
    print("🔨 Building BM25 index...")

    retriever = BM25Retriever.from_documents(docs)
    retriever.k = k

    print(f"✅ BM25 index built! {len(docs)} chunks indexed")
    return retriever