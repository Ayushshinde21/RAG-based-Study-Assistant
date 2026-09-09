from dotenv import load_dotenv
load_dotenv()

from core.chunker import chunk_text
from core.vector_store import build_vector_store, get_dense_retriever
from core.bm25_index import build_bm25_retriever
from core.hybrid_retriever import hybrid_retrieve

dummy = """
Machine learning is a subset of artificial intelligence. It allows systems to learn
from data without being explicitly programmed. There are three main types of machine
learning: supervised learning, unsupervised learning, and reinforcement learning.

Supervised learning uses labeled data to train models. Common algorithms include
linear regression, decision trees, and neural networks. The model learns to map
inputs to outputs based on example input-output pairs.

Unsupervised learning finds hidden patterns in data without labels. Clustering
algorithms like K-means group similar data points together. Dimensionality reduction
techniques like PCA reduce the number of features while preserving information.

Reinforcement learning trains agents to make decisions by rewarding good actions
and penalizing bad ones. It is used in game playing, robotics, and self-driving cars.
"""

# Phase 4 - Chunk
docs = chunk_text(dummy, source="test_lecture", method="fixed")

# Phase 5 - Index
vector_store    = build_vector_store(docs)
dense_retriever = get_dense_retriever(vector_store, k=3)
bm25_retriever  = build_bm25_retriever(docs, k=3)

# Test retrieval
query   = "What is supervised learning?"
results = hybrid_retrieve(query, dense_retriever, bm25_retriever, top_n=3)

print(f"\n✅ Phase 5 Complete!")
print(f"\nTop {len(results)} results for: '{query}'")
for i, doc in enumerate(results):
    print(f"\n--- Result {i+1} ---")
    print(doc.page_content[:200])