# DermaCare Project Startup Script
# Comprehensive setup and launch of both backend and frontend

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "DermaCare - Skin Detection AI Project" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Color helper
function Write-Status {
    param([string]$Message, [string]$Color = "Green")
    Write-Host "[✓] $Message" -ForegroundColor $Color
}

function Write-Error-Status {
    param([string]$Message)
    Write-Host "[✗] $Message" -ForegroundColor Red
}

# Check Python environment
Write-Host "Checking Python environment..." -ForegroundColor Yellow
$pythonExe = "$scriptDir/venv/Scripts/python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Error-Status "Python venv not found! Run: python -m venv venv"
    exit 1
}
Write-Status "Python environment ready"

# Verify dependencies
Write-Host ""
Write-Host "Verifying dependencies..." -ForegroundColor Yellow
& $pythonExe -c 'import torch; print("PyTorch version:", torch.__version__)' | out-null
if ($LASTEXITCODE -eq 0) {
    Write-Status "All dependencies installed"
}
else {
    Write-Error-Status "Missing dependencies. Installing..."
    & $pythonExe -m pip install -r backend/requirements.txt -q
}

Write-Host ""

# Start backend
if (-not $FrontendOnly) {
    Write-Host "Starting Backend Server..." -ForegroundColor Yellow
    Write-Host "Backend will run at: http://localhost:$BackendPort" -ForegroundColor Cyan
    Write-Host ""

    # Check if model exists
    $modelPath = "$scriptDir/backend/ml/best_model.pth"
    if (-not (Test-Path $modelPath)) {
        Write-Error-Status "No trained model found!"
        Write-Host "Model expected at: $modelPath" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "To train the model, run:" -ForegroundColor Cyan
        Write-Host "  python -m backend.ml.train" -ForegroundColor Green
        Write-Host ""
        Write-Host "Continuing with inference-only mode (using fallback heuristics)..." -ForegroundColor Yellow
    }
    else {
        Write-Status "Trained model found and ready"
    }

    Write-Host ""
    & $pythonExe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port $BackendPort
}

# Note: Frontend should be started in a separate terminal
if (-not $BackendOnly) {
    Write-Host ""
    Write-Host "To start the frontend in another terminal, run:" -ForegroundColor Cyan
    Write-Host "  cd frontend; npm install; npm run dev" -ForegroundColor Green
    Write-Host "Frontend will run at: http://localhost:$FrontendPort" -ForegroundColor Cyan
}
