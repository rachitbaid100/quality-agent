from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_tcagent
from tcagent.cache import LocalCache
from tcagent.models import GenerationInput


class RunnerTest(unittest.TestCase):
    def test_export_cached_excel_missing_key(self):
        with patch("run_tcagent.DEFAULT_CACHE_PATH", Path("missing-cache.json")):
            self.assertEqual(run_tcagent.export_cached_excel("missing", None), 1)

    def test_export_cached_excel_present_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            output_path = Path(tmpdir) / "cases.xlsx"
            data = GenerationInput("Story", "Criteria", "llama3.2:3b")
            result = {"summary": "Story", "test_cases": []}
            LocalCache(cache_path).set(data, result)
            key = LocalCache(cache_path)._read_entries()[0].key

            with patch("run_tcagent.DEFAULT_CACHE_PATH", cache_path):
                status = run_tcagent.export_cached_excel(key, output_path)

            self.assertEqual(status, 0)
            self.assertTrue(output_path.exists())

    def test_export_cached_excel_skips_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            output_path = Path(tmpdir) / "cases.xlsx"
            output_path.write_text("existing", encoding="utf-8")
            data = GenerationInput("Story", "Criteria", "llama3.2:3b")
            result = {"summary": "Story", "test_cases": []}
            LocalCache(cache_path).set(data, result)
            key = LocalCache(cache_path)._read_entries()[0].key

            with patch("run_tcagent.DEFAULT_CACHE_PATH", cache_path):
                status = run_tcagent.export_cached_excel(key, output_path)

            self.assertEqual(status, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "existing")


if __name__ == "__main__":
    unittest.main()
