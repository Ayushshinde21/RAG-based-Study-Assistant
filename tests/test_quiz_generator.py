import json
import unittest
from unittest.mock import patch

from langchain_core.documents import Document
from features.quiz_generator import build_quiz_prompt, generate_quiz


class TestQuizPrompt(unittest.TestCase):
    def test_prompt_builds_json_example_without_formatting_error(self):
        prompt = build_quiz_prompt("A binary tree has nodes and edges.", 5)

        self.assertIn('Generate exactly 5 multiple-choice questions', prompt)
        self.assertIn('"questions": [', prompt)
        self.assertIn('"A": "First option"', prompt)
        self.assertIn('"D": "Fourth option"', prompt)
        self.assertIn("A binary tree has nodes and edges.", prompt)

    def test_prompt_example_is_valid_json(self):
        prompt = build_quiz_prompt("Lecture content", 3)
        start = prompt.index('{\n  "questions"')
        end = prompt.index('\n\nUse only information supported', start)
        example = json.loads(prompt[start:end])

        self.assertIn("questions", example)
        self.assertEqual(set(example["questions"][0]["options"]), {"A", "B", "C", "D"})


    def test_generate_quiz_builds_prompt_and_parses_questions(self):
        response = {
            "questions": [
                {
                    "question": "What does a binary tree node contain?",
                    "options": {
                        "A": "Data and links to child nodes",
                        "B": "Only a database table",
                        "C": "Only a sorting function",
                        "D": "A network address",
                    },
                    "answer": "A",
                    "explanation": "A node stores data and may reference its children.",
                }
            ]
        }

        class FakeLLM:
            def __init__(self):
                self.prompt = ""

            def invoke(self, prompt):
                self.prompt = prompt
                return json.dumps(response)

        fake_llm = FakeLLM()
        with patch("features.quiz_generator.get_llm", return_value=fake_llm):
            questions = generate_quiz(
                [Document(page_content="A binary tree node stores data and child links.")],
                num_questions=1,
            )

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]["answer"], "A")
        self.assertIn('"questions": [', fake_llm.prompt)


if __name__ == "__main__":
    unittest.main()
