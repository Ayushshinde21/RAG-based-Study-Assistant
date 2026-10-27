import json

from core.llm import get_groq_llm, response_text
from langchain_core.documents import Document


def get_llm(*, response_mime_type: str | None = None):
    return get_groq_llm(response_mime_type=response_mime_type)


def build_quiz_prompt(lecture_text: str, num_questions: int) -> str:
    """Build the quiz-generation prompt without interpolating JSON braces."""
    example = {
        "questions": [
            {
                "question": "What is the main concept?",
                "options": {
                    "A": "First option",
                    "B": "Second option",
                    "C": "Third option",
                    "D": "Fourth option",
                },
                "answer": "A",
                "explanation": "Explanation based on the lecture.",
            }
        ]
    }
    example_json = json.dumps(example, ensure_ascii=False, indent=2)

    return f"""You are an AI study assistant.
Generate exactly {num_questions} multiple-choice questions from the lecture content below.
Each question must have 4 options (A, B, C, D) and exactly one correct answer.

Return ONLY a valid JSON object, with no explanation outside the JSON and no Markdown fences.
The object must contain a top-level "questions" array, as shown in this example:
{example_json}

Use only information supported by the lecture content. Make the wrong options plausible and do not repeat questions.

--- LECTURE CONTENT ---
{lecture_text}

--- JSON OUTPUT ---"""


def generate_quiz(docs: list[Document], num_questions: int = 5, max_chunks: int = 15) -> list[dict]:
    if not docs:
        raise ValueError("No documents to generate quiz from")

    docs_to_use = docs[:max_chunks] if len(docs) > max_chunks else docs
    full_text = "\n\n".join([doc.page_content for doc in docs_to_use])

    max_chars = 10000
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars]

    prompt = build_quiz_prompt(full_text, num_questions)

    llm = get_llm(response_mime_type="application/json")
    response = llm.invoke(prompt)
    raw = response_text(response)
    if not raw:
        print("⚠️ Quiz generator returned an empty response")
        return []
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            questions = payload.get("questions")
        elif isinstance(payload, list):
            # Accept older model responses that returned the questions array directly.
            questions = payload
        else:
            questions = None

        if not isinstance(questions, list):
            raise ValueError("Response does not contain a questions array")

        if len(questions) != num_questions:
            raise ValueError(
                f"Expected {num_questions} questions, received {len(questions)}"
            )

        required_keys = {"question", "options", "answer", "explanation"}

        for question in questions:
            if not isinstance(question, dict) or not required_keys.issubset(question):
                raise ValueError("A quiz question is missing required fields")

            if not isinstance(question["question"], str) or not question["question"].strip():
                raise ValueError("Question text must be a non-empty string")

            if not isinstance(question["options"], dict):
                raise ValueError("Question options must be a JSON object")

            if set(question["options"]) != {"A", "B", "C", "D"}:
                raise ValueError("Each question must have options A, B, C and D")

            if any(
                not isinstance(option, str) or not option.strip()
                for option in question["options"].values()
            ):
                raise ValueError("Each answer option must be a non-empty string")

            if question["answer"] not in {"A", "B", "C", "D"}:
                raise ValueError("Question answer must be A, B, C or D")

        print(f"Quiz generated! {len(questions)} questions")
        return questions

    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Quiz response validation failed: {exc}")
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
