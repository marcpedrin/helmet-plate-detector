#!/usr/bin/env bash
# Start the frontend dev server (bash / Git Bash).
set -euo pipefail
cd "$(dirname "$0")/../frontend"
exec npm run dev
