from core.chunker import chunk_text

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

docs = chunk_text(dummy, source="test_lecture", method="semantic")
print(f"\nTotal chunks: {len(docs)}")
for i, doc in enumerate(docs):
    print(f"\nChunk {i+1}:")
    print(doc.page_content)
    print(f"Metadata: {doc.metadata}")