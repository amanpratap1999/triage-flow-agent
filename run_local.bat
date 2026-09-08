@echo off
echo ==========================================
echo  Starting Support Ticket Triage Agent
echo ==========================================

if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
    call .\venv\Scripts\pip install -r requirements.txt
)

if not exist .env (
    copy .env.example .env
)

echo Starting FastAPI server at http://127.0.0.1:8002
echo Ops Dashboard: http://127.0.0.1:8002
echo Swagger Docs: http://127.0.0.1:8002/docs
echo Health Check: http://127.0.0.1:8002/health

call .\venv\Scripts\uvicorn src.main:app --host 127.0.0.1 --port 8002 --reload
pause
