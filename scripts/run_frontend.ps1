# Start the frontend dev server (Windows PowerShell).
$ErrorActionPreference = "Stop"
Set-Location (Join-Path (Split-Path -Parent $PSScriptRoot) "frontend")
npm run dev
