"""Regression tests for the duplicated-file problem: every source file
should define each top-level function/class exactly once."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "tests", "chroma_db"}


def source_files():
    for path in ROOT.rglob("*.py"):
        if not SKIP_DIRS.intersection(path.parts):
            yield path


class TestNoDuplicateDefinitions(unittest.TestCase):
    def test_top_level_names_unique(self):
        problems = []
        for path in source_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            seen = set()
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if node.name in seen:
                        problems.append(f"{path.relative_to(ROOT)}: {node.name}")
                    seen.add(node.name)
        self.assertEqual(problems, [], "Duplicate top-level definitions found")

    def test_no_empty_source_files(self):
        empty = [str(p.relative_to(ROOT)) for p in source_files()
                 if p.name != "__init__.py" and not p.read_text(encoding="utf-8").strip()]
        self.assertEqual(empty, [])


if __name__ == "__main__":
    unittest.main()
