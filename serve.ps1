# Serve the repo from THIS folder so /showcase/ and /output/ URLs resolve.
# Usage: right-click -> Run with PowerShell, OR:  powershell -ExecutionPolicy Bypass -File serve.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$port = 8765
Write-Host "Open in browser:" -ForegroundColor Green
Write-Host "  http://localhost:$port/showcase/index.html" -ForegroundColor Cyan
Write-Host "  http://localhost:$port/  (redirects to showcase)" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow
Start-Process "http://localhost:$port/showcase/index.html"
python -m http.server $port
