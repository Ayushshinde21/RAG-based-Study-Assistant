from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma


def reciprocal_rank_fusion(
    dense_results: list[Document],
    bm25_results: list[Document],
    k: int = 60
) -> list[Document]:
    """
    Combine dense + BM25 results using Reciprocal Rank Fusion (RRF).
    RRF gives higher scores to documents that rank well in both lists.
    Returns merged and re-ranked list.
    """
    scores = {}
    doc_map = {}

    # score dense results
    for rank, doc in enumerate(dense_results):
        key = doc.page_content
        scores[key] = scores.get(key, 0) + 1 / (k + rank + 1)
        doc_map[key] = doc

    # score BM25 results
    for rank, doc in enumerate(bm25_results):
        key = doc.page_content
        scores[key] = scores.get(key, 0) + 1 / (k + rank + 1)
        doc_map[key] = doc

    # sort by combined score
    sorted_keys = sorted(scores, key=scores.get, reverse=True)
    return [doc_map[key] for key in sorted_keys]


def hybrid_retrieve(
    query: str,
    dense_retriever,
    bm25_retriever: BM25Retriever,
    top_n: int = 10
) -> list[Document]:
    """
    Main retrieval function.
    Queries both dense and BM25 retrievers,
    combines results with RRF, returns top_n.
    """
    print(f"🔍 Retrieving for: '{query}'")

    # get results from both
    dense_results  = dense_retriever.invoke(query)
    bm25_results   = bm25_retriever.invoke(query)

    print(f"   Dense results : {len(dense_results)}")
    print(f"   BM25 results  : {len(bm25_results)}")

    # combine with RRF
    merged = reciprocal_rank_fusion(dense_results, bm25_results)
    final  = merged[:top_n]

    print(f"   After RRF     : {len(final)} chunks")
    return final