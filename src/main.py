import logging
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.config import settings
from src.database import engine, get_db, Base
from src.models import Ticket, ToolExecution
from src.schemas import (
    TicketCreate,
    TicketResponse,
    TicketEscalationAction,
    QueueStats,
    HealthResponse
)
from src.agent import run_triage_pipeline
from src.tools import lookup_order, lookup_account, check_refund_eligibility

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("triage_agent")

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Support Ticket Triage & Resolution Agent",
    description="Autonomous customer support ticket triage with multi-tool calling and human-in-the-loop escalation.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error. Please consult logs."}
    )

@app.get("/", include_in_schema=False)
def serve_dashboard():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Support Ticket Triage Agent API"}

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check(db: Session = Depends(get_db)):
    return HealthResponse(
        status="ok",
        database="sqlite-connected",
        llm_mode="mock" if settings.MOCK_LLM else "live",
        version="0.1.0"
    )

@app.post("/tickets", response_model=TicketResponse, status_code=201, tags=["Tickets"])
async def create_and_triage_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    """
    Ingest customer support ticket, execute autonomous triage pipeline, and save resolution state.
    """
    logger.info(f"Ingesting ticket from {payload.customer_email}: '{payload.subject}'")
    
    # 1. Run Autonomous Decision Graph
    result = await run_triage_pipeline(
        customer_email=payload.customer_email,
        subject=payload.subject,
        body=payload.body
    )

    # 2. Persist Ticket
    ticket = Ticket(
        customer_email=payload.customer_email,
        subject=payload.subject,
        body=payload.body,
        category=result.category,
        status=result.status,
        confidence=result.confidence,
        resolution_text=result.resolution_text,
        escalation_reason=result.escalation_reason,
        recommended_action=result.recommended_action
    )
    db.add(ticket)
    db.flush()

    # 3. Persist Tool Execution Traces
    for trace in result.tool_traces:
        tool_rec = ToolExecution(
            ticket_id=ticket.id,
            tool_name=trace["tool_name"],
            tool_input=trace["tool_input"],
            tool_output=trace["tool_output"]
        )
        db.add(tool_rec)

    db.commit()
    db.refresh(ticket)
    return ticket

@app.get("/tickets", response_model=List[TicketResponse], tags=["Tickets"])
def list_tickets(status: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    List tickets with optional status filter ('resolved' or 'escalated').
    """
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    return query.order_by(desc(Ticket.id)).all()

@app.get("/tickets/{ticket_id}", response_model=TicketResponse, tags=["Tickets"])
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket

@app.post("/tickets/{ticket_id}/action", response_model=TicketResponse, tags=["Human-in-the-Loop"])
def human_escalation_action(ticket_id: int, payload: TicketEscalationAction, db: Session = Depends(get_db)):
    """
    Human reviewer resolution endpoint for escalated tickets.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    ticket.human_action = payload.action
    ticket.human_notes = payload.notes
    
    if payload.action == "approve_resolution":
        ticket.status = "resolved"
        ticket.resolution_text = payload.notes or "Escalation approved by human supervisor."
    elif payload.action == "reject":
        ticket.status = "closed_rejected"
    elif payload.action == "manual_reply":
        ticket.status = "resolved"
        ticket.resolution_text = payload.notes

    db.commit()
    db.refresh(ticket)
    return ticket

@app.get("/queue/stats", response_model=QueueStats, tags=["System"])
def get_queue_stats(db: Session = Depends(get_db)):
    total = db.query(Ticket).count()
    resolved = db.query(Ticket).filter(Ticket.status == "resolved").count()
    escalated = db.query(Ticket).filter(Ticket.status == "escalated").count()
    pending = db.query(Ticket).filter(Ticket.status == "pending").count()
    rate = (resolved / total * 100) if total > 0 else 0.0
    
    return QueueStats(
        total_tickets=total,
        resolved_count=resolved,
        escalated_count=escalated,
        pending_count=pending,
        resolution_rate=round(rate, 1)
    )

# --- STUB TOOL DIRECT API ENDPOINTS ---
@app.get("/tools/orders/{order_id}", tags=["Mock Tools"])
def api_lookup_order(order_id: str):
    return lookup_order(order_id)

@app.get("/tools/accounts/{email}", tags=["Mock Tools"])
def api_lookup_account(email: str):
    return lookup_account(email)

@app.get("/tools/refunds/eligibility", tags=["Mock Tools"])
def api_check_refund(order_id: str, days: Optional[int] = None):
    return check_refund_eligibility(order_id, days_since_purchase=days)
