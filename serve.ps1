# Serve site from THIS folder. Opens browser AFTER the server starts (avoids ERR_CONNECTION_REFUSED).
# Usage: powershell -ExecutionPolicy Bypass -File .\serve.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$port = 8765

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "python not found in PATH. Install Python or use full path." -ForegroundColor Red
    exit 1
}

Write-Host "Starting http://localhost:$port/ (project root) ..." -ForegroundColor Green
Write-Host "Press Ctrl+C in this window to stop the server." -ForegroundColor Yellow

# Open browser ~1.5s after server begins (server starts on next line — schedule open in parallel)
Start-Job -ScriptBlock {
    Start-Sleep -Milliseconds 1600
    Start-Process "http://localhost:$using:port/"
} | Out-Null

python -m http.server $port
