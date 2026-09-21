from dotenv import load_dotenv
load_dotenv()

from utils.audio_processor import get_audio_path
from utils.transcriber import transcribe, save_transcript
from core.chunker import chunk_from_file
from core.vector_store import build_vector_store, get_dense_retriever
from core.bm25_index import build_bm25_retriever
from core.rag_engine import RAGEngine
from features.summarizer import summarize
from features.quiz_generator import generate_quiz, display_quiz

print("Step 1: Get audio")
# ── Step 1: Get audio ─────────────────────────────────────────────────────────
audio = get_audio_path(r"C:\Users\frmxg\Downloads\deep_learning_high_res.mp4")

print("Step 2: Transcribe")
# ── Step 2: Transcribe ────────────────────────────────────────────────────────
transcript = transcribe(audio)
transcript_path = save_transcript(transcript, audio)

print("Step 3: Chunk")
# ── Step 3: Chunk ─────────────────────────────────────────────────────────────
docs = chunk_from_file(transcript_path, method="semantic")

print("Step 4: Index")
# ── Step 4: Index ─────────────────────────────────────────────────────────────
vector_store    = build_vector_store(docs)
dense_retriever = get_dense_retriever(vector_store, k=10)
bm25_retriever  = build_bm25_retriever(docs, k=10)

print("Step 5: RAG Engine")
# ── Step 5: RAG Engine ────────────────────────────────────────────────────────
rag = RAGEngine(dense_retriever, bm25_retriever)

# ── Step 6: Summarize ─────────────────────────────────────────────────────────
print("\n📋 LECTURE SUMMARY")
print("=" * 50)
summary = summarize(docs)
print(summary)

# ── Step 7: Quiz ──────────────────────────────────────────────────────────────
print("\n📝 AUTO QUIZ")
questions = generate_quiz(docs, num_questions=5)
display_quiz(questions)

# ── Step 8: Live Q&A ──────────────────────────────────────────────────────────
print("\n💬 ASK QUESTIONS (type 'exit' to stop)")
print("=" * 50)
while True:
    query = input("\nYour question: ").strip()
    if query.lower() in ["exit", "quit", "q"]:
        break
    if not query:
        continue
    answer = rag.answer(query)
    print(f"\n🤖 Answer:\n{answer}")