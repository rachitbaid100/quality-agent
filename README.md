# TC-Agent V1

TC-Agent V1 generates the first set of QA test cases from a user story and acceptance criteria using a local Ollama 3B model. Results are cached locally, so repeated or highly similar inputs can return without another model call.

## Features

- Uses Ollama locally.
- Defaults to `llama3.2:3b`.
- Imports Apple's `mlx` library when available for local Apple Silicon runtime visibility.
- Accepts user story and acceptance criteria from CLI flags or interactive input.
- Stores cached generations in `.tca_cache/cache.json`.
- Returns cached results for exact or similar prompts.
- Outputs JSON by default, with Markdown as an option.
- Keeps the prompt compact to reduce token usage.

## Setup

Recommended:

```bash
./setup.sh
source .venv/bin/activate
```

`setup.sh` installs Ollama with Homebrew if needed. If the Homebrew formula is missing `llama-server`, it installs the official Ollama app bundle and uses `/Applications/Ollama.app/Contents/Resources/ollama`.

Manual:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
ollama pull llama3.2:3b
```

Minimal dependency install without editable project setup:

```bash
python3 -m pip install -r requirements.txt
```

Optional model override:

```bash
export TCA_MODEL="llama3.2:3b"
```

Optional Ollama URL override:

```bash
export TCA_OLLAMA_URL="http://127.0.0.1:11434"
```

Runtime check:

```bash
python3 -m tcagent --runtime-info
```

Ollama connectivity check:

```bash
python3 -m tcagent --doctor
```

Make sure the Ollama app or service is running before generating test cases.

## Usage

Simple runner:

Edit [run_tcagent.py](run_tcagent.py), then set:

```python
story = "some story"
criteria = "some criteria"
```

Run:

```bash
python3 run_tcagent.py
```

Export a cached result to Excel:

```bash
python3 run_tcagent.py --excel --cachekey="value of cache key"
```

If the cache key is not present, the command exits without generating test cases.

Interactive mode:

```bash
python3 -m tcagent
```

Non-interactive mode:

```bash
python3 -m tcagent \
  --story "A new login page supports Google, Apple, and Facebook login" \
  --criteria "Users can sign in with each provider. Failed provider auth returns user to login page. Successful login redirects to dashboard."
```

Markdown output:

```bash
python3 -m tcagent --format markdown
```

Force a fresh Ollama generation and update the cache:

```bash
python3 -m tcagent --no-cache
```

Adjust similarity matching:

```bash
python3 -m tcagent --similarity-threshold 0.97
```

## Run Tests

```bash
python3 -m unittest discover
```
