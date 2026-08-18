# ─────────────────────────────────────────────────────────────────────────────
# DermaCare - Full Stack Launcher
# Starts FastAPI backend (port 8000) + Next.js frontend (port 3000)
# ─────────────────────────────────────────────────────────────────────────────

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       DermaCare AI Launcher          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ─── Backend ──────────────────────────────────────────────────────────────────
Write-Host "[1/2] Starting FastAPI backend on http://localhost:8000 ..." -ForegroundColor Yellow

$BackendCmd = @"
Set-Location '$Root'
& '$Root\venv\Scripts\python.exe' -m uvicorn main:app --reload --port 8000 --app-dir '$Root\backend'
"@

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $BackendCmd

Start-Sleep -Seconds 2

# ─── Frontend ─────────────────────────────────────────────────────────────────
Write-Host "[2/2] Starting Next.js frontend on http://localhost:3000 ..." -ForegroundColor Green

$FrontendCmd = @"
Set-Location '$Root\frontend'
npm run dev
"@

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $FrontendCmd

Write-Host ""
Write-Host "✅  Both servers are starting up!" -ForegroundColor Cyan
Write-Host "   Frontend → http://localhost:3000" -ForegroundColor White
Write-Host "   Backend  → http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs → http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
