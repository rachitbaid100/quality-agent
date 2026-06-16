cat > setup.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"
OLLAMA_MODEL="${TCA_MODEL:-llama3.2:3b}"
OLLAMA_URL="${TCA_OLLAMA_URL:-http://127.0.0.1:11434}"
OLLAMA_APP_BIN="/Applications/Ollama.app/Contents/Resources/ollama"
OLLAMA_LOG="/tmp/quality-agent-ollama.log"

cd "${PROJECT_DIR}"

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required."
  echo "Install Homebrew from https://brew.sh, then rerun ./setup.sh"
  exit 1
fi

resolve_python_bin() {
  for candidate in python3.12 python3.11 /opt/homebrew/bin/python3.11 /usr/local/bin/python3.11; do
    if command -v "${candidate}" >/dev/null 2>&1 || [[ -x "${candidate}" ]]; then
      if "${candidate}" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
      then
        echo "${candidate}"
        return
      fi
    fi
  done

  echo "Python 3.11+ not found. Installing python@3.11 via Homebrew..." >&2
  brew install python@3.11 >&2

  for candidate in /opt/homebrew/bin/python3.11 /usr/local/bin/python3.11 python3.11; do
    if command -v "${candidate}" >/dev/null 2>&1 || [[ -x "${candidate}" ]]; then
      echo "${candidate}"
      return
    fi
  done

  echo "Python 3.11 installation failed." >&2
  exit 1
}

PYTHON_BIN="$(resolve_python_bin)"

echo "Using Python binary: ${PYTHON_BIN}"
"${PYTHON_BIN}" --version

echo "Recreating virtualenv with Python 3.11+..."
rm -rf "${VENV_DIR}"
"${PYTHON_BIN}" -m venv "${VENV_DIR}"

source "${VENV_DIR}/bin/activate"

echo "Virtualenv Python:"
python --version

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .

formula_has_llama_server() {
  if ! brew --prefix ollama >/dev/null 2>&1; then
    return 1
  fi

  local prefix
  prefix="$(brew --prefix ollama)"
  find "${prefix}" -name llama-server -type f -perm -111 | grep -q .
}

ensure_ollama_app() {
  if [[ -x "${OLLAMA_APP_BIN}" ]]; then
    return
  fi

  echo "Installing official Ollama app bundle..."
  brew install --cask ollama-app
}

resolve_ollama_bin() {
  if [[ -n "${TCA_OLLAMA_BIN:-}" ]]; then
    echo "${TCA_OLLAMA_BIN}"
    return
  fi

  if [[ -x "${OLLAMA_APP_BIN}" ]]; then
    echo "${OLLAMA_APP_BIN}"
    return
  fi

  if formula_has_llama_server; then
    command -v ollama
    return
  fi

  ensure_ollama_app
  echo "${OLLAMA_APP_BIN}"
}

validate_ollama_generation() {
  curl -fsS "${OLLAMA_URL}/api/generate" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"${OLLAMA_MODEL}\",\"prompt\":\"Return only: ok\",\"stream\":false}" \
    >/dev/null
}

OLLAMA_BIN="$(resolve_ollama_bin)"

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install -e .

if ! curl -fsS "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
  nohup "${OLLAMA_BIN}" serve >"${OLLAMA_LOG}" 2>&1 &
fi

for _ in {1..30}; do
  if curl -fsS "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
  echo "Ollama did not become ready at ${OLLAMA_URL}."
  echo "Check ${OLLAMA_LOG}, then run: ${OLLAMA_BIN} serve"
  exit 1
fi

"${OLLAMA_BIN}" pull "${OLLAMA_MODEL}"

if ! validate_ollama_generation; then
  echo "Ollama is reachable, but generation failed."
  echo "A broken listener may already be running at ${OLLAMA_URL}."
  echo "Stop the current listener, then restart with:"
  echo "${OLLAMA_BIN} serve"
  exit 1
fi

echo "Setup complete."
echo "Run: source .venv/bin/activate"
echo "Then run: python run_quality_agent.py"
EOF

chmod +x setup.sh
rm -rf .venv
./setup.sh