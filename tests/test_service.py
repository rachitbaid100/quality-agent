from pathlib import Path
import tempfile
import unittest

from tcagent.models import GenerationInput
from tcagent.service import generate_test_cases, generate_test_cases_text


def fake_generator(data: GenerationInput):
    return {
        "summary": f"Generated with {data.model}",
        "test_cases": [
            {
                "title": "Verify happy path",
                "category": "positive",
                "priority": "P1",
                "preconditions": [],
                "steps": [],
                "expected_result": "Success",
            }
        ],
    }


class ServiceTest(unittest.TestCase):
    def test_generates_and_caches_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_test_cases(
                "Login story",
                "User can login",
                model="llama3.2:3b",
                cache_path=Path(tmpdir) / "cache.json",
                generator=fake_generator,
            )

            self.assertFalse(result["_cache"]["hit"])
            self.assertEqual(result["summary"], "Generated with llama3.2:3b")

    def test_reuses_cached_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"

            generate_test_cases(
                "Login story",
                "User can login",
                model="llama3.2:3b",
                cache_path=cache_path,
                generator=fake_generator,
            )
            cached = generate_test_cases(
                "Login story",
                "User can login",
                model="llama3.2:3b",
                cache_path=cache_path,
                generator=fake_generator,
            )

            self.assertTrue(cached["_cache"]["hit"])
            self.assertEqual(cached["_cache"]["match_type"], "exact")

    def test_renders_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = generate_test_cases_text(
                "Login story",
                "User can login",
                model="llama3.2:3b",
                cache_path=Path(tmpdir) / "cache.json",
                generator=fake_generator,
            )

            self.assertIn("Generated with llama3.2:3b", output)

    def test_rejects_missing_input(self):
        with self.assertRaises(ValueError):
            generate_test_cases("", "criteria", generator=fake_generator)


if __name__ == "__main__":
    unittest.main()
