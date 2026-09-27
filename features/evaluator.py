import os
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

import numpy as np

def evaluate_rag(
    questions: list[str],
    answers: list[str],
    contexts: list[list[str]],
    ground_truths: list[str]
) -> dict:
    """
    Evaluate RAG system using RAGAS framework with Groq LLM.
    """
    print("📊 Running RAGAS evaluation...")

    # tell RAGAS to use Groq instead of OpenAI
    groq_llm = ChatGroq(
        model="llama-3.1-8b-instant",  # same as rag_engine.py
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.0,
    )
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )

    ragas_llm        = LangchainLLMWrapper(groq_llm)
    ragas_embeddings = LangchainEmbeddingsWrapper(embeddings)

    data = {
        "question":     questions,
        "answer":       answers,
        "contexts":     contexts,
        "ground_truth": ground_truths,
    }

    dataset = Dataset.from_dict(data)

    metrics = [
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ]

    # assign LLM and embeddings to each metric
    for metric in metrics:
        metric.llm        = ragas_llm
        metric.embeddings = ragas_embeddings

    result = evaluate(dataset, metrics=metrics)

    scores = {
        "faithfulness": round(float(np.mean(result["faithfulness"])), 3),
        "answer_relevancy": round(float(np.mean(result["answer_relevancy"])), 3),
        "context_precision": round(float(np.mean(result["context_precision"])), 3),
        "context_recall": round(float(np.mean(result["context_recall"])), 3),
    }

    print("\n📊 RAGAS Evaluation Results:")
    print("-" * 35)
    for metric, score in scores.items():
        bar = "█" * int(score * 20)
        print(f"  {metric:<22} {score:.3f}  {bar}")
    print("-" * 35)

    return scores


def quick_evaluate(rag_engine, test_qa: list[dict]) -> dict:
    """
    Convenience function — runs evaluation from a list of QA pairs.

    test_qa format:
    [
        {"question": "...", "ground_truth": "..."},
        ...
    ]
    """
    from core.hybrid_retriever import hybrid_retrieve
    from core.reranker import rerank

    questions     = []
    answers       = []
    contexts      = []
    ground_truths = []

    for qa in test_qa:
        q  = qa["question"]
        gt = qa["ground_truth"]

        # get answer from RAG engine
        answer = rag_engine.answer(q)

        # get contexts used
        retrieved = hybrid_retrieve(
            q,
            rag_engine.dense_retriever,
            rag_engine.bm25_retriever,
            top_n=5
        )
        reranked = rerank(q, retrieved, top_n=3)
        ctx = [doc.page_content for doc in reranked]

        questions.append(q)
        answers.append(answer)
        contexts.append(ctx)
        ground_truths.append(gt)

    return evaluate_rag(questions, answers, contexts, ground_truths)
