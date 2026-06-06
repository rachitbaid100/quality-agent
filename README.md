# quality-agent

quality-agent is a local test case generation tool for QA and SDET workflows. It takes a user story plus acceptance criteria, generates structured test cases with a local Ollama model, caches results on disk, and can export cached test cases to Excel.

The project is designed to avoid paid LLM APIs for V1. Generation runs locally through Ollama, with `llama3.2:3b` as the default model.

## Features

- Local LLM generation through Ollama.
- Default model: `llama3.2:3b`.
- JSON output by default.
- Markdown output option.
- File-based cache for exact and similar prompts.
- Excel export from cached results.
- Optional Apple MLX runtime check on Apple Silicon.
- No OpenAI API key required.

## Requirements

- Python 3.10+
- Ollama
- `llama3.2:3b` model pulled locally
- macOS with Homebrew for the current `setup.sh`

The core Python app talks to Ollama over `http://127.0.0.1:11434`, so it can be extended to Linux and Windows later. The current setup automation is macOS-oriented.

## Setup

Recommended:

```bash
./setup.sh
source .venv/bin/activate
```

`setup.sh` installs Python dependencies, resolves a healthy Ollama binary, starts the Ollama service, pulls the configured model, and validates actual generation. On macOS, it prefers the official Ollama app bundle because that includes the required `llama-server` runtime:

```bash
/Applications/Ollama.app/Contents/Resources/ollama
```

The Homebrew formula is used only when it has the required `llama-server` runtime. If an existing listener responds to `/api/tags` but fails `/api/generate`, setup reports how to stop and restart Ollama with the healthy binary.

Manual setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
/Applications/Ollama.app/Contents/Resources/ollama pull llama3.2:3b
```

Correct macOS command to start the Ollama server:

```bash
/Applications/Ollama.app/Contents/Resources/ollama serve
```

Use this fixed path instead of plain `ollama serve` when the Homebrew formula is missing `llama-server`.

## Usage

Edit [run_tcagent.py](run_tcagent.py), then set:

```python
story = "A new login page supports Google, Apple, and Facebook login"
criteria = "Users can sign in with each provider. Failed provider auth returns user to login page. Successful login redirects to dashboard."
```

Run:

```bash
python3 run_tcagent.py
```

Interactive CLI:

```bash
quality-agent
```

Non-interactive CLI:

```bash
quality-agent \
  --story "A new login page supports Google, Apple, and Facebook login" \
  --criteria "Users can sign in with each provider. Failed provider auth returns user to login page. Successful login redirects to dashboard."
```

Markdown output:

```bash
quality-agent --format markdown
```

## Caching

quality-agent stores generated results in:

```text
.tca_cache/cache.json
```

Each cache entry contains:

- `key`: SHA-256 hash for exact cache lookup.
- `normalized_text`: cleaned user story and criteria for similarity lookup.
- `model`: model used for generation.
- `prompt_version`: prompt template version.
- `result`: generated test cases.
- `created_at`: UTC timestamp.

If the same input is used again, quality-agent returns the cached result without calling Ollama. If the input is similar enough, quality-agent can also reuse a previous result.

Force fresh generation:

```bash
quality-agent --no-cache
```

Adjust similarity threshold:

```bash
quality-agent --similarity-threshold 0.97
```

## Excel Export

Export a cached result to Excel:

```bash
python3 run_tcagent.py --excel --cachekey="value of cache key"
```

Default output:

```text
exports/test-cases-<cachekey-prefix>.xlsx
```

If the cache key is missing, quality-agent prints:

```text
Cache key not present.
```

If the Excel file already exists, quality-agent does not overwrite it.

## Diagnostics

Check Ollama connectivity:

```bash
quality-agent --doctor
```

Check local runtime information:

```bash
quality-agent --runtime-info
```

Override the Ollama model:

```bash
export TCA_MODEL="llama3.2:3b"
```

Override the Ollama URL:

```bash
export TCA_OLLAMA_URL="http://127.0.0.1:11434"
```

Override the Ollama binary:

```bash
export TCA_OLLAMA_BIN="/Applications/Ollama.app/Contents/Resources/ollama"
```

## Troubleshooting

If you see `llama-server binary not found`, your Homebrew Ollama formula is missing required runtime files. Use the official app-bundled binary:

```bash
/Applications/Ollama.app/Contents/Resources/ollama serve
```

If port `11434` is already in use:

```bash
lsof -nP -iTCP:11434
kill <PID>
```

If Ollama is not reachable, confirm the service is running:

```bash
quality-agent --doctor
```

## Project Structure

```text
tcagent/
  cache.py            # file-based cache
  cli.py              # command-line interface
  excel_exporter.py   # cached JSON to XLSX export
  ollama_client.py    # local Ollama generation client
  prompt.py           # compact prompt template
  service.py          # generation orchestration
run_tcagent.py        # simple editable runner
setup.sh              # macOS setup helper
tests/                # unit tests
```

## Development

Run tests:

```bash
python3 -m unittest discover
```

Install editable package:

```bash
python3 -m pip install -e .
```

The legacy module command still works:

```bash
python3 -m tcagent
```

## Git Ignore Policy

The repo ignores local runtime artifacts:

- `.venv/`
- `.tca_cache/`
- `exports/`
- `vault/`
- Python bytecode and build outputs

Generated cache files, Excel files, and vault secrets should not be committed.
