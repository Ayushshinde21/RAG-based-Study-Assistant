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

    try:
        # "low" skips most of the model's internal reasoning pass — this is
        # lookup-style Q&A, not a task that needs deep reasoning, and cutting
        # reasoning effort is the single biggest latency win available here.
        # Needs a recent langchain-groq; fall back cleanly on older versions.
        return ChatGroq(
            model="openai/gpt-oss-20b",
            api_key=api_key,
            temperature=0.2,
            reasoning_effort="low",
        )
    except TypeError:
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
    def _label(doc, i):
        ts = doc.metadata.get("start_time_str")
        return f"[Chunk {i+1} — around {ts}]" if ts else f"[Chunk {i+1}]"

    context = "\n\n".join([
        f"{_label(doc, i)}:\n{doc.page_content}"
        for i, doc in enumerate(context_docs)
    ])

    prompt = f"""You are a helpful AI study assistant. 
Your job is to answer student questions based ONLY on the lecture content provided below.
If the answer is not in the lecture content, say "I could not find this in the lecture."
Do not make up information.
When a chunk includes a timestamp (e.g. "around 14:32"), you may mention it in
your answer (e.g. "this is covered around 14:32") so the student can find it
in the recording — but never invent a timestamp for a chunk that has none.

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

    def _invoke_with_retry(self, prompt: str, max_attempts: int = 3):
        """
        Call the LLM with retry on transient errors —
        rate limits (429), server errors (500/502/503), and timeouts.
        Reads the API's own retry-after when present instead of a flat 60s
        sleep, and caps waits so one slow retry can't freeze the whole UI.
        """
        import re

        transient_markers = ["429", "500", "502", "503", "timeout"]

        for attempt in range(max_attempts):
            try:
                return self.llm.invoke(prompt)
            except Exception as e:
                err_str = str(e).lower()
                is_transient = any(m in err_str for m in transient_markers)

                if is_transient and attempt < max_attempts - 1:
                    wait = 5
                    retry_after = getattr(getattr(e, "response", None), "headers", {}).get("retry-after")
                    if retry_after:
                        try:
                            wait = min(float(retry_after), 15)
                        except ValueError:
                            pass
                    else:
                        m = re.search(r"try again in ([\d.]+)s", err_str)
                        if m:
                            wait = min(float(m.group(1)), 15)
                    print(f"⏳ Transient error hit — waiting {wait}s (attempt {attempt+1}/{max_attempts})...")
                    time.sleep(wait)
                else:
                    raise e

    def answer_with_sources(self, query: str, use_memory: bool = True):
        """
        Main entry point.
        Takes a student question → retrieves → reranks → generates answer.
        Returns (answer, reranked_docs) so the UI can show real sources
        and evaluation can score exactly what the answer was built from.
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
        chat_history = ""
        if use_memory:
            messages = self.memory.messages[-MEMORY_WINDOW:]
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
        if use_memory:
            self.memory.add_user_message(query)
            self.memory.add_ai_message(answer)

        print(f"✅ Answer generated!")
        return answer, reranked

    def answer(self, query: str) -> str:
        """Back-compat wrapper — returns just the answer text."""
        answer, _ = self.answer_with_sources(query)
        return answer

    def prepare_stream(self, query: str, use_memory: bool = True):
        """
        Does retrieval + reranking + prompt-building (same as
        answer_with_sources), but returns a generator for the answer instead
        of waiting for the full response — lets the UI show the first words
        almost immediately instead of one long blocking spinner.
        Returns (token_generator, reranked_docs, save_fn). Call save_fn(answer)
        once the caller has consumed the generator, to commit it to memory.
        """
        from core.hybrid_retriever import hybrid_retrieve
        from core.reranker import rerank

        retrieved = hybrid_retrieve(query, self.dense_retriever, self.bm25_retriever, top_n=10)
        reranked = rerank(query, retrieved, top_n=5)

        chat_history = ""
        if use_memory:
            messages = self.memory.messages[-MEMORY_WINDOW:]
            for msg in messages:
                role = "Student" if msg.type == "human" else "Assistant"
                chat_history += f"{role}: {msg.content}\n"

        prompt = build_prompt(query, reranked, chat_history)

        def token_generator():
            for chunk in self.llm.stream(prompt):
                text = getattr(chunk, "content", "") or ""
                if text:
                    yield text

        def save_fn(full_answer: str):
            if use_memory:
                self.memory.add_user_message(query)
                self.memory.add_ai_message(full_answer)

        return token_generator(), reranked, save_fn

    def reset_memory(self):
        self.memory.clear()
        print("🔄 Memory cleared")
