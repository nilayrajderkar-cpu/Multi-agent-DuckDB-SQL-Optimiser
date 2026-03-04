#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Setting up Python backend environment"
cd "${ROOT_DIR}/backend"

if [ ! -d ".venv" ]; then
  echo "Creating virtualenv in backend/.venv"
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

pip install --upgrade pip >/dev/null
pip install -r requirements.txt

echo "==> Ensuring frontend dependencies are installed"
cd "${ROOT_DIR}"
if [ ! -d "node_modules" ]; then
  npm install
fi

echo "==> Starting backend (FastAPI / prem-1B-SQL)"
cd "${ROOT_DIR}/backend"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "==> Starting frontend (Vite + React)"
cd "${ROOT_DIR}"
npm run dev &
FRONTEND_PID=$!

cleanup() {
  echo
  echo "Shutting down dev servers..."
  kill "${BACKEND_PID}" "${FRONTEND_PID}" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo
echo "Dev environment running:"
echo "  Frontend: http://localhost:5173"
echo "  Backend : http://127.0.0.1:8000"
echo "Press Ctrl+C to stop both."

wait

