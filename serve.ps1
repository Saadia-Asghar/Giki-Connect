# Start GIKI-Connect Flask app (model-backed UI on http://127.0.0.1:8765/)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "python not found in PATH." -ForegroundColor Red
    exit 1
}

Write-Host "Starting GIKI-Connect app at http://127.0.0.1:8765/ ..." -ForegroundColor Green
Write-Host "Install deps once:  pip install flask scikit-learn joblib numpy" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow

Start-Job -ScriptBlock {
    Start-Sleep -Milliseconds 2000
    Start-Process "http://127.0.0.1:8765/"
} | Out-Null

python app_server.py
