# Support Ticket Triage & Resolution Agent (Project 2)

> **Autonomous AI/ML Portfolio — Multi-Tool Agent**  
> Autonomous customer support triage agent that resolves repetitive inquiries (60–70%) and escalates edge cases with diagnostic reasoning to a human supervisor queue.

---

## Quickstart (Run Cold in 60 Seconds)

### Option A: 1-Click Windows Launch (PowerShell)
```powershell
.\run_local.ps1
```
*(Or double-click `run_local.bat`)*

### Option B: Manual Setup
1. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
3. **Run the server:**
   ```powershell
   uvicorn src.main:app --host 127.0.0.1 --port 8002 --reload
   ```

Open your browser to:
- **Ops Dashboard:** [http://127.0.0.1:8002](http://127.0.0.1:8002)
- **Interactive Swagger Docs:** [http://127.0.0.1:8002/docs](http://127.0.0.1:8002/docs)
- **Health Check:** [http://127.0.0.1:8002/health](http://127.0.0.1:8002/health)

---

## Running Tests & Benchmark Evaluation

### 1. Run Automated Unit & Integration Tests
```powershell
.\venv\Scripts\pytest -v tests/
```

### 2. Run the 32-Ticket Evaluation Benchmark
```powershell
.\venv\Scripts\python eval/run_eval.py
```
This tests autonomous resolution rates, safe escalation rates, and the critical false-resolution rate across 32 synthetic customer tickets.

---

## API Endpoints & Examples

### 1. Ingest Support Ticket for Autonomous Triage
```bash
curl -X POST http://127.0.0.1:8002/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "jane@example.com",
    "subject": "Where is my order ORD-101?",
    "body": "Can you check tracking for ORD-101? I need to know when it arrives."
  }'
```
**Response (Resolved):**
```json
{
  "id": 1,
  "customer_email": "jane@example.com",
  "subject": "Where is my order ORD-101?",
  "category": "order_inquiry",
  "status": "resolved",
  "confidence": 0.95,
  "resolution_text": "Hello! Your order (ORD-101) is currently in transit via FedEx under tracking number FX-884920194. Estimated delivery is scheduled for Tomorrow by 5:00 PM.",
  "escalation_reason": null,
  "tool_executions": [
    {
      "id": 1,
      "tool_name": "lookup_order",
      "tool_input": "{\"order_id\": \"ORD-101\"}",
      "tool_output": "{\"success\": true, \"order\": {...}}",
      "created_at": "2026-09-08T12:00:00"
    }
  ]
}
```

### 2. Ambiguous or Policy Exception Ticket (Escalated)
```bash
curl -X POST http://127.0.0.1:8002/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "mark@example.com",
    "subject": "Refund ORD-103",
    "body": "I want a refund for ORD-103. I bought it 45 days ago."
  }'
```
**Response (Escalated to Human):**
```json
{
  "id": 2,
  "status": "escalated",
  "confidence": 0.88,
  "escalation_reason": "Policy Exception: Order was placed 45 days ago, exceeding the strict 30-day customer return policy.",
  "recommended_action": "Manager review required: determine whether to issue a one-time store credit courtesy."
}
```

### 3. Human Reviewer Action Endpoint
```bash
curl -X POST http://127.0.0.1:8002/tickets/2/action \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve_resolution",
    "notes": "Manager approved one-time store credit exception."
  }'
```

---

## Directory Structure
```
project-2-triage-agent/
├── .env.example
├── .gitignore
├── ARCHITECTURE.md
├── BUILD_LOG.md
├── DECISIONS.md
├── Dockerfile
├── docker-compose.yml
├── README.md
├── requirements.txt
├── run_local.bat
├── run_local.ps1
├── src/
│   ├── __init__.py
│   ├── agent.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── tools.py
├── static/
│   └── index.html
├── tests/
│   └── test_triage.py
├── eval/
│   ├── dataset.json
│   └── run_eval.py
└── docs/
    └── eval-results.md
```
