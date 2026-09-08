from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr

class TicketCreate(BaseModel):
    customer_email: str = Field(..., description="Customer email address")
    subject: str = Field(..., min_length=3, max_length=255, description="Ticket subject line")
    body: str = Field(..., min_length=5, description="Customer issue or request message")

class ToolExecutionTrace(BaseModel):
    id: int
    tool_name: str
    tool_input: str
    tool_output: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TicketResponse(BaseModel):
    id: int
    customer_email: str
    subject: str
    body: str
    category: str
    status: str
    confidence: float
    resolution_text: Optional[str] = None
    escalation_reason: Optional[str] = None
    recommended_action: Optional[str] = None
    human_action: Optional[str] = None
    human_notes: Optional[str] = None
    created_at: datetime
    tool_executions: List[ToolExecutionTrace] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class TicketEscalationAction(BaseModel):
    action: str = Field(..., description="Action to take: 'approve_resolution', 'reject', or 'manual_reply'")
    notes: Optional[str] = Field(None, description="Human reviewer notes or custom reply")

class QueueStats(BaseModel):
    total_tickets: int
    resolved_count: int
    escalated_count: int
    pending_count: int
    resolution_rate: float

class HealthResponse(BaseModel):
    status: str
    database: str
    llm_mode: str
    version: str
