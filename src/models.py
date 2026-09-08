import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    
    category = Column(String(50), nullable=False, default="general_inquiry")
    status = Column(String(50), nullable=False, default="pending")  # 'resolved', 'escalated', 'pending'
    confidence = Column(Float, nullable=False, default=0.0)
    
    resolution_text = Column(Text, nullable=True)
    escalation_reason = Column(Text, nullable=True)
    recommended_action = Column(String(255), nullable=True)
    
    # Human-in-the-loop tracking
    human_action = Column(String(100), nullable=True)  # 'approved', 'rejected', 'manual_reply'
    human_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    tool_executions = relationship("ToolExecution", back_populates="ticket", cascade="all, delete-orphan")


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    tool_name = Column(String(100), nullable=False)
    tool_input = Column(Text, nullable=False)
    tool_output = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="tool_executions")
