import os
import time
from langchain_core.documents import Document
from langchain_community.chat_message_histories import ChatMessageHistory

# how many messages to keep in memory (5 exchanges = 10 messages: 5 user + 5 assistant)
MEMORY_WINDOW = 10


# ── LLM setup ─────────────────────────────────────────────────────────────────

def get_llm():
    from langchain_groq import ChatGroq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env")

    return ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=api_key,
        temperature=0.2,
    )


# ── Memory ────────────────────────────────────────────────────────────────────

def get_memory():
    """
    Simple chat history — keeps last few exchanges.
    """
    return ChatMessageHistory()


# ── Prompt ────────────────────────────────────────────────────────────────────

def build_prompt(query: str, context_docs: list[Document],
                 chat_history: str) -> str:
    context = "\n\n".join([
        f"[Chunk {i+1}]:\n{doc.page_content}"
        for i, doc in enumerate(context_docs)
    ])

    prompt = f"""You are a helpful AI study assistant. 
Your job is to answer student questions based ONLY on the lecture content provided below.
If the answer is not in the lecture content, say "I could not find this in the lecture."
Do not make up information.

--- LECTURE CONTENT ---
{context}

--- CONVERSATION HISTORY ---
{chat_history if chat_history else "No previous conversation."}

--- STUDENT QUESTION ---
{query}

--- YOUR ANSWER ---"""

    return prompt


# ── Main RAG function ─────────────────────────────────────────────────────────

class RAGEngine:
    """
    Main RAG engine — combines retrieval, reranking, and generation.
    Maintains conversation memory across questions.
    """

    def __init__(self, dense_retriever, bm25_retriever):
        self.dense_retriever = dense_retriever
        self.bm25_retriever  = bm25_retriever
        self.llm             = get_llm()
        self.memory          = get_memory()
        print("✅ RAG Engine initialized")

    def _invoke_with_retry(self, prompt: str, max_attempts: int = 5):
        """
        Call the LLM with retry on transient errors —
        rate limits (429), server errors (500/502/503), and timeouts.
        """
        transient_markers = ["429", "500", "502", "503", "timeout"]

        for attempt in range(max_attempts):
            try:
                return self.llm.invoke(prompt)
            except Exception as e:
                err_str = str(e).lower()
                is_transient = any(m in err_str for m in transient_markers)

                if is_transient and attempt < max_attempts - 1:
                    wait = 60 if "429" in err_str else 10
                    print(f"⏳ Transient error hit — waiting {wait}s (attempt {attempt+1}/{max_attempts})...")
                    time.sleep(wait)
                else:
                    raise e

    def answer(self, query: str) -> str:
        """
        Main entry point.
        Takes a student question → retrieves → reranks → generates answer.
        """
        from core.hybrid_retriever import hybrid_retrieve
        from core.reranker import rerank

        print(f"\n💬 Question: {query}")

        # Step 1 — Hybrid retrieval (top 10)
        retrieved = hybrid_retrieve(
            query,
            self.dense_retriever,
            self.bm25_retriever,
            top_n=10
        )

        # Step 2 — Rerank (top 5)
        reranked = rerank(query, retrieved, top_n=5)

        # Step 3 — Get chat history
        messages = self.memory.messages[-MEMORY_WINDOW:]
        chat_history = ""
        for msg in messages:
            role = "Student" if msg.type == "human" else "Assistant"
            chat_history += f"{role}: {msg.content}\n"

        # Step 4 — Build prompt
        prompt = build_prompt(query, reranked, chat_history)

        # Step 5 — Generate answer (with retry)
        print("🤖 Generating answer...")
        response = self._invoke_with_retry(prompt)
        answer = response.content.strip()

        # Step 6 — Save to memory
        self.memory.add_user_message(query)
        self.memory.add_ai_message(answer)

        print(f"✅ Answer generated!")
        return answer

    def reset_memory(self):
        self.memory.clear()
        print("🔄 Memory cleared")
import os
import time
from langchain_core.documents import Document
from langchain_community.chat_message_histories import ChatMessageHistory

# how many messages to keep in memory (5 exchanges = 10 messages: 5 user + 5 assistant)
MEMORY_WINDOW = 10


# ── LLM setup ─────────────────────────────────────────────────────────────────

def get_llm():
    from langchain_groq import ChatGroq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env")

    return ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=api_key,
        temperature=0.2,
    )


# ── Memory ────────────────────────────────────────────────────────────────────

def get_memory():
    """
    Simple chat history — keeps last few exchanges.
    """
    return ChatMessageHistory()


# ── Prompt ────────────────────────────────────────────────────────────────────

def build_prompt(query: str, context_docs: list[Document],
                 chat_history: str) -> str:
    context = "\n\n".join([
        f"[Chunk {i+1}]:\n{doc.page_content}"
        for i, doc in enumerate(context_docs)
    ])

    prompt = f"""You are a helpful AI study assistant. 
Your job is to answer student questions based ONLY on the lecture content provided below.
If the answer is not in the lecture content, say "I could not find this in the lecture."
Do not make up information.

--- LECTURE CONTENT ---
{context}

--- CONVERSATION HISTORY ---
{chat_history if chat_history else "No previous conversation."}

--- STUDENT QUESTION ---
{query}

--- YOUR ANSWER ---"""

    return prompt


# ── Main RAG function ─────────────────────────────────────────────────────────

class RAGEngine:
    """
    Main RAG engine — combines retrieval, reranking, and generation.
    Maintains conversation memory across questions.
    """

    def __init__(self, dense_retriever, bm25_retriever):
        self.dense_retriever = dense_retriever
        self.bm25_retriever  = bm25_retriever
        self.llm             = get_llm()
        self.memory          = get_memory()
        print("✅ RAG Engine initialized")

    def _invoke_with_retry(self, prompt: str, max_attempts: int = 5):
        """
        Call the LLM with retry on transient errors —
        rate limits (429), server errors (500/502/503), and timeouts.
        """
        transient_markers = ["429", "500", "502", "503", "timeout"]

        for attempt in range(max_attempts):
            try:
                return self.llm.invoke(prompt)
            except Exception as e:
                err_str = str(e).lower()
                is_transient = any(m in err_str for m in transient_markers)

                if is_transient and attempt < max_attempts - 1:
                    wait = 60 if "429" in err_str else 10
                    print(f"⏳ Transient error hit — waiting {wait}s (attempt {attempt+1}/{max_attempts})...")
                    time.sleep(wait)
                else:
                    raise e

    def answer(self, query: str) -> str:
        """
        Main entry point.
        Takes a student question → retrieves → reranks → generates answer.
        """
        from core.hybrid_retriever import hybrid_retrieve
        from core.reranker import rerank

        print(f"\n💬 Question: {query}")

        # Step 1 — Hybrid retrieval (top 10)
        retrieved = hybrid_retrieve(
            query,
            self.dense_retriever,
            self.bm25_retriever,
            top_n=10
        )

        # Step 2 — Rerank (top 5)
        reranked = rerank(query, retrieved, top_n=5)

        # Step 3 — Get chat history
        messages = self.memory.messages[-MEMORY_WINDOW:]
        chat_history = ""
        for msg in messages:
            role = "Student" if msg.type == "human" else "Assistant"
            chat_history += f"{role}: {msg.content}\n"

        # Step 4 — Build prompt
        prompt = build_prompt(query, reranked, chat_history)

        # Step 5 — Generate answer (with retry)
        print("🤖 Generating answer...")
        response = self._invoke_with_retry(prompt)
        answer = response.content.strip()

        # Step 6 — Save to memory
        self.memory.add_user_message(query)
        self.memory.add_ai_message(answer)

        print(f"✅ Answer generated!")
        return answer

    def reset_memory(self):
        self.memory.clear()
        print("🔄 Memory cleared")
