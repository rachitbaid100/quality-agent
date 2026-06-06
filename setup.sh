#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"
OLLAMA_MODEL="${TCA_MODEL:-llama3.2:3b}"
OLLAMA_URL="${TCA_OLLAMA_URL:-http://127.0.0.1:11434}"
OLLAMA_APP_BIN="/Applications/Ollama.app/Contents/Resources/ollama"

cd "${PROJECT_DIR}"

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required to install Ollama automatically."
  echo "Install Homebrew from https://brew.sh, then rerun ./setup.sh"
  exit 1
fi

if ! command -v ollama >/dev/null 2>&1; then
  brew install ollama
fi

OLLAMA_PREFIX="$(brew --prefix ollama)"
if ! find "${OLLAMA_PREFIX}" -name llama-server -type f -perm -111 | grep -q .; then
  echo "Homebrew Ollama formula is missing llama-server. Installing Ollama app bundle..."
  brew install --cask ollama-app
fi

if [[ -x "${OLLAMA_APP_BIN}" ]] && ! find "${OLLAMA_PREFIX}" -name llama-server -type f -perm -111 | grep -q .; then
  OLLAMA_BIN="${OLLAMA_APP_BIN}"
else
  OLLAMA_BIN="$(command -v ollama)"
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install -e .

if ! curl -fsS "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
  nohup "${OLLAMA_BIN}" serve >/tmp/tcagent-ollama.log 2>&1 &
fi

for _ in {1..30}; do
  if curl -fsS "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
  echo "Ollama did not become ready at ${OLLAMA_URL}."
  echo "Check /tmp/tcagent-ollama.log, then run: ollama serve"
  exit 1
fi

"${OLLAMA_BIN}" pull "${OLLAMA_MODEL}"

echo "Setup complete."
echo "Run: source .venv/bin/activate"
echo "Then run: python3 run_tcagent.py"
