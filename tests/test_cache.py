from pathlib import Path
import tempfile
import unittest

from tcagent.cache import LocalCache
from tcagent.models import GenerationInput


class LocalCacheTest(unittest.TestCase):
    def test_exact_cache_hit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LocalCache(Path(tmpdir) / "cache.json")
            data = GenerationInput("Login with Google", "User can login successfully", "llama3.2:3b")
            result = {"summary": "Login", "test_cases": []}

            cache.set(data, result)
            hit = cache.get(data, similarity_threshold=0.94)

            self.assertIsNotNone(hit)
            self.assertEqual(hit.match_type, "exact")
            self.assertEqual(hit.result, result)

    def test_similar_cache_hit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LocalCache(Path(tmpdir) / "cache.json")
            original = GenerationInput(
                "New login page supports Google, Apple, and Facebook login",
                "Users can sign in with each provider",
                "llama3.2:3b",
            )
            similar = GenerationInput(
                "The new login page supports Google, Apple and Facebook sign in",
                "Users can sign in with every provider",
                "llama3.2:3b",
            )

            cache.set(original, {"summary": "Social login", "test_cases": []})
            hit = cache.get(similar, similarity_threshold=0.80)

            self.assertIsNotNone(hit)
            self.assertEqual(hit.match_type, "similar")


if __name__ == "__main__":
    unittest.main()
