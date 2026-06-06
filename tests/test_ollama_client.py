import json
from io import BytesIO
import urllib.error
import unittest
from unittest.mock import patch

from quality_agent.models import GenerationInput
from quality_agent.ollama_client import LocalGenerationError, generate_with_ollama, get_ollama_command, get_ollama_tags, parse_model_json


class ParseModelJsonTest(unittest.TestCase):
    def test_parses_valid_payload(self):
        payload = parse_model_json('{"summary":"Login","test_cases":[]}')

        self.assertEqual(payload["summary"], "Login")
        self.assertEqual(payload["test_cases"], [])

    def test_extracts_json_from_wrapped_output(self):
        payload = parse_model_json('Here is JSON: {"summary":"Login","test_cases":[]}')

        self.assertEqual(payload["summary"], "Login")

    def test_rejects_invalid_json(self):
        with self.assertRaises(LocalGenerationError):
            parse_model_json("not json")

    def test_rejects_missing_test_cases(self):
        with self.assertRaises(LocalGenerationError):
            parse_model_json('{"summary":"Login"}')


class GenerateWithOllamaTest(unittest.TestCase):
    def test_posts_to_ollama_and_parses_response(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps(
                    {"response": '{"summary":"Login","test_cases":[]}'}
                ).encode("utf-8")

        data = GenerationInput("story", "criteria", "llama3.2:3b")
        with patch("urllib.request.urlopen", return_value=FakeResponse()):
            payload = generate_with_ollama(data)

        self.assertEqual(payload["summary"], "Login")

    def test_falls_back_to_ollama_cli_when_http_unreachable(self):
        class FakeCompleted:
            returncode = 0
            stdout = '{"summary":"Login","test_cases":[]}'
            stderr = ""

        data = GenerationInput("story", "criteria", "llama3.2:3b")
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("blocked")):
            with patch("quality_agent.ollama_client.get_ollama_command", return_value="/opt/homebrew/bin/ollama"):
                with patch("subprocess.run", return_value=FakeCompleted()):
                    payload = generate_with_ollama(data)

        self.assertEqual(payload["summary"], "Login")

    def test_explains_missing_llama_server_http_error(self):
        class FakeHTTPError(urllib.error.HTTPError):
            def read(self):
                return b'{"error":"llama-server binary not found"}'

        data = GenerationInput("story", "criteria", "llama3.2:3b")
        error = FakeHTTPError(
            "http://127.0.0.1:11434/api/generate",
            500,
            "Internal Server Error",
            {},
            BytesIO(),
        )

        with patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(LocalGenerationError, "incomplete Homebrew formula"):
                generate_with_ollama(data)

    def test_prefers_app_binary_when_path_install_is_missing_runtime(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("os.path.exists", return_value=True):
                with patch("quality_agent.ollama_client._path_install_has_llama_server", return_value=False):
                    self.assertEqual(
                        get_ollama_command(),
                        "/Applications/Ollama.app/Contents/Resources/ollama",
                    )

    def test_reads_ollama_tags(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps({"models": [{"name": "llama3.2:3b"}]}).encode("utf-8")

        with patch("urllib.request.urlopen", return_value=FakeResponse()):
            tags = get_ollama_tags()

        self.assertEqual(tags["models"][0]["name"], "llama3.2:3b")


if __name__ == "__main__":
    unittest.main()
