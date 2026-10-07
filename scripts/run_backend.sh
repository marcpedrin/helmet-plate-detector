#!/usr/bin/env bash
# Start the backend (bash / Git Bash). Run from anywhere.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "$ROOT/backend/.venv/Scripts/activate" ]; then source "$ROOT/backend/.venv/Scripts/activate"; else source "$ROOT/backend/.venv/bin/activate"; fi
cd "$ROOT/backend"
exec uvicorn app.main:app --host 127.0.0.1 --port 8000
