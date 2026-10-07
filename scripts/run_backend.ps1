# Start the backend (Windows PowerShell). Run from anywhere.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
& "$root\backend\.venv\Scripts\Activate.ps1"
Set-Location "$root\backend"
uvicorn app.main:app --host 127.0.0.1 --port 8000
