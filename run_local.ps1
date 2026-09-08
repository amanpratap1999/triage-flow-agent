# Local PowerShell runner for Project 2: Support Ticket Triage Agent
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Starting Support Ticket Triage Agent     " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    .\venv\Scripts\pip install -r requirements.txt
}

if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
}

Write-Host "Starting FastAPI server on http://127.0.0.1:8002 ..." -ForegroundColor Green
Write-Host "Ops Dashboard: http://127.0.0.1:8002" -ForegroundColor Green
Write-Host "Swagger Docs: http://127.0.0.1:8002/docs" -ForegroundColor Green
Write-Host "Health Check: http://127.0.0.1:8002/health" -ForegroundColor Green

.\venv\Scripts\uvicorn src.main:app --host 127.0.0.1 --port 8002 --reload
