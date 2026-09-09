import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# persistent storage folder
CHROMA_DIR = "chroma_db"

def get_embeddings():
    """
    Load HuggingFace embedding model.
    """
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )


def build_vector_store(docs: list[Document]) -> Chroma:
    """
    Build ChromaDB vector store from documents.
    Saves to disk so it persists between runs.
    """
    print("🔨 Building ChromaDB vector store...")

    embeddings = get_embeddings()

    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name="lecture_chunks"
    )

    print(f"✅ Vector store built! {len(docs)} chunks indexed")
    return vector_store


def load_vector_store() -> Chroma:
    """
    Load existing ChromaDB from disk.
    """
    if not os.path.exists(CHROMA_DIR):
        raise FileNotFoundError("No vector store found. Run build first.")

    embeddings = get_embeddings()

    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name="lecture_chunks"
    )

    print(f"✅ Vector store loaded from disk")
    return vector_store


def get_dense_retriever(vector_store: Chroma, k: int = 10):
    """
    Get dense retriever from vector store.
    Returns top-k most similar chunks.
    """
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )