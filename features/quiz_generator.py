import os
import json
from langchain_groq import ChatGroq
from langchain_core.documents import Document


def get_llm():
    return ChatGroq(
        model="groq/compound",  # replace with your working model
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.5,   # slightly higher for variety
    )


def generate_quiz(docs: list[Document], num_questions: int = 5, max_chunks: int = 15) -> list[dict]:
    if not docs:
        raise ValueError("No documents to generate quiz from")

    docs_to_use = docs[:max_chunks] if len(docs) > max_chunks else docs
    full_text = "\n\n".join([doc.page_content for doc in docs_to_use])

    max_chars = 10000
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars]

    prompt = f"""You are an AI study assistant.
Generate exactly {num_questions} multiple choice questions from the lecture content below.
Each question must have 4 options (A, B, C, D) and one correct answer.

Return ONLY a valid JSON array, no explanation, no markdown, just the JSON.

Format:
[
  {{
    "question": "Question text here?",
    "options": {{
      "A": "Option A",
      "B": "Option B", 
      "C": "Option C",
      "D": "Option D"
    }},
    "answer": "A",
    "explanation": "Brief explanation of why this is correct"
  }}
]

--- LECTURE CONTENT ---
{full_text}

--- JSON OUTPUT ---"""

    llm = get_llm()
    response = llm.invoke(prompt)
    raw = response.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        questions = json.loads(raw)
        print(f"✅ Quiz generated! {len(questions)} questions")
        return questions
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parse error: {e}")
        print(f"Raw response: {raw[:200]}")
        return []


def display_quiz(questions: list[dict]):
    """
    Print quiz in a readable format.
    """
    print("\n" + "=" * 50)
    print("📝 AUTO-GENERATED QUIZ")
    print("=" * 50)

    for i, q in enumerate(questions):
        print(f"\nQ{i+1}. {q['question']}")
        for key, val in q['options'].items():
            print(f"   {key}. {val}")
        print(f"   ✅ Answer: {q['answer']}")
        print(f"   💡 {q['explanation']}")
import os
import json
from langchain_groq import ChatGroq
from langchain_core.documents import Document


def get_llm():
    return ChatGroq(
        model="groq/compound",  # replace with your working model
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.5,   # slightly higher for variety
    )


def generate_quiz(docs: list[Document], num_questions: int = 5, max_chunks: int = 15) -> list[dict]:
    if not docs:
        raise ValueError("No documents to generate quiz from")

    docs_to_use = docs[:max_chunks] if len(docs) > max_chunks else docs
    full_text = "\n\n".join([doc.page_content for doc in docs_to_use])

    max_chars = 10000
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars]

    prompt = f"""You are an AI study assistant.
Generate exactly {num_questions} multiple choice questions from the lecture content below.
Each question must have 4 options (A, B, C, D) and one correct answer.

Return ONLY a valid JSON array, no explanation, no markdown, just the JSON.

Format:
[
  {{
    "question": "Question text here?",
    "options": {{
      "A": "Option A",
      "B": "Option B", 
      "C": "Option C",
      "D": "Option D"
    }},
    "answer": "A",
    "explanation": "Brief explanation of why this is correct"
  }}
]

--- LECTURE CONTENT ---
{full_text}

--- JSON OUTPUT ---"""

    llm = get_llm()
    response = llm.invoke(prompt)
    raw = response.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        questions = json.loads(raw)
        print(f"✅ Quiz generated! {len(questions)} questions")
        return questions
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parse error: {e}")
        print(f"Raw response: {raw[:200]}")
        return []


def display_quiz(questions: list[dict]):
    """
    Print quiz in a readable format.
    """
    print("\n" + "=" * 50)
    print("📝 AUTO-GENERATED QUIZ")
    print("=" * 50)

    for i, q in enumerate(questions):
        print(f"\nQ{i+1}. {q['question']}")
        for key, val in q['options'].items():
            print(f"   {key}. {val}")
        print(f"   ✅ Answer: {q['answer']}")
        print(f"   💡 {q['explanation']}")
