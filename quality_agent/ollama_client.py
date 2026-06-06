from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from typing import Any

from .models import GenerationInput
from .prompt import build_generation_prompt


DEFAULT_MODEL = "llama3.2:3b"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
APP_OLLAMA_BIN = "/Applications/Ollama.app/Contents/Resources/ollama"


class LocalGenerationError(RuntimeError):
    pass


def get_default_model() -> str:
    return os.getenv("TCA_MODEL", DEFAULT_MODEL)


def get_ollama_url() -> str:
    return os.getenv("TCA_OLLAMA_URL", DEFAULT_OLLAMA_URL).rstrip("/")


def get_ollama_command() -> str | None:
    configured = os.getenv("TCA_OLLAMA_BIN")
    if configured:
        return configured
    if os.path.exists(APP_OLLAMA_BIN) and not _path_install_has_llama_server():
        return APP_OLLAMA_BIN
    return shutil.which("ollama")


def _path_install_has_llama_server() -> bool:
    command = shutil.which("ollama")
    if not command:
        return False
    candidates = [
        os.path.realpath(os.path.join(os.path.dirname(command), "..", "opt", "ollama")),
        os.path.realpath(os.path.join(os.path.dirname(command), "..", "Cellar", "ollama")),
    ]
    for root in candidates:
        if not os.path.exists(root):
            continue
        for directory, _, files in os.walk(root):
            if "llama-server" in files:
                return True
    return False


def get_ollama_tags() -> dict[str, Any]:
    url = f"{get_ollama_url()}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise LocalGenerationError(f"Ollama tags endpoint is not reachable at {url}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LocalGenerationError(f"Ollama tags endpoint returned invalid JSON at {url}.") from exc


def generate_with_ollama(data: GenerationInput) -> dict[str, Any]:
    payload = {
        "model": data.model,
        "prompt": build_generation_prompt(data),
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_predict": 1800,
        },
    }

    request = urllib.request.Request(
        f"{get_ollama_url()}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if "llama-server binary not found" in detail:
            raise LocalGenerationError(
                "Ollama is running from an incomplete Homebrew formula install. "
                "Stop the current listener, then run "
                "`/Applications/Ollama.app/Contents/Resources/ollama serve`."
            ) from exc
        raise LocalGenerationError(
            f"Ollama returned HTTP {exc.code} from {request.full_url}: {detail}"
        ) from exc
    except urllib.error.URLError:
        return generate_with_ollama_cli(data)

    try:
        response_payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LocalGenerationError("Ollama returned invalid JSON from its API.") from exc

    if "error" in response_payload:
        raise LocalGenerationError(str(response_payload["error"]))

    return parse_model_json(str(response_payload.get("response", "")))


def generate_with_ollama_cli(data: GenerationInput) -> dict[str, Any]:
    ollama_command = get_ollama_command()
    if not ollama_command:
        raise LocalGenerationError(
            "Ollama HTTP API is not reachable and the `ollama` command was not found."
        )

    try:
        completed = subprocess.run(
            [ollama_command, "run", data.model, build_generation_prompt(data)],
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired as exc:
        raise LocalGenerationError("Ollama CLI generation timed out.") from exc

    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise LocalGenerationError(f"Ollama CLI generation failed: {message}")

    return parse_model_json(completed.stdout)


def parse_model_json(output_text: str) -> dict[str, Any]:
    output_text = output_text.strip()
    if not output_text:
        raise LocalGenerationError("Ollama returned an empty response.")

    try:
        payload = json.loads(output_text)
    except json.JSONDecodeError:
        payload = _extract_json_object(output_text)

    if not isinstance(payload, dict) or not isinstance(payload.get("test_cases"), list):
        raise LocalGenerationError("Model JSON must contain a test_cases array.")

    return payload


def _extract_json_object(output_text: str) -> dict[str, Any]:
    start = output_text.find("{")
    end = output_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LocalGenerationError("Model did not return valid JSON.")

    try:
        return json.loads(output_text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LocalGenerationError("Model did not return valid JSON.") from exc
