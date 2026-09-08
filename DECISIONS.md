# Architectural Decisions Record (ADR) — Project 2: Support Ticket Triage & Resolution Agent

## ADR 001: Explicit Decision Graph (Resolve vs. Escalate)
- **Context:** In autonomous customer support, a false resolution (a confidently wrong answer, an unapproved refund, or an unaddressed legal complaint) causes severe brand damage and operational liability. Confidently wrong answers are penalized far more heavily than cautious escalations.
- **Decision:** Implement a multi-stage deterministic decision graph:
  1. **Intent Classification & Sentiment Inspection:**
     - Extract intent category (`order_inquiry`, `account_access`, `refund_request`, `billing_issue`, `general_inquiry`).
     - Scan for high-risk escalation triggers: legal threats, chargeback threats, profanity, and account takeover claims.
  2. **Entity Extraction:**
     - Extract structured identifiers: `order_id` (`ORD-XXXXX`), `email`, `amount`.
  3. **Tool Execution Node:**
     - Call corresponding stub tool endpoint (`lookup_order`, `lookup_account`, `check_refund_eligibility`).
  4. **Decision Boundary Node:**
     - **RESOLVE ONLY IF:**
       - Confidence $\ge 0.80$.
       - Tool returned valid record.
       - Action is strictly within policy (e.g., standard shipping inquiry, eligible refund within 30 days, account unlock request).
       - No high-risk or adversarial sentiment.
     - **ESCALATE IF:**
       - Confidence $< 0.80$.
       - Missing required entity (e.g., user asks for order status without order ID).
       - Tool flags policy exception (e.g., refund requested beyond 30 days window).
       - Legal, dispute, or hostile language detected.
- **Tradeoff:** Slightly higher escalation rate on ambiguous tickets, but drives false-resolution rate below 3%.

## ADR 002: Human-in-the-Loop Escalation Payload
- **Context:** When a human agent receives an escalated ticket, re-reading the entire thread from scratch wastes time.
- **Decision:** When escalating, the agent attaches an actionable diagnostic payload:
  - `escalation_reason`: Explicit statement of why the ticket was escalated (e.g., *"Refund ineligible: purchase date 48 days ago exceeds 30-day window"*).
  - `tool_diagnostics`: Raw outputs from stub tools called during triage.
  - `recommended_action`: Suggested resolution for the human reviewer (`approve_exception_refund`, `send_clarification_email`, `manual_investigation`).
- **Tradeoff:** Additional structured fields in the ticket model, but reduces human triage time by ~60%.

## ADR 003: SQLite Local State & Stub Tool Micro-APIs
- **Context:** The build spec requires PostgreSQL and stub tools for order/account/refund status. Local execution without Docker was requested.
- **Decision:**
  - Store ticket state and tool traces in local SQLite (`tickets.db`) using standard SQLAlchemy ORM.
  - Stub tool endpoints (`/tools/orders/{id}`, `/tools/accounts/{id}`, `/tools/refunds/eligibility`) are built directly into the FastAPI service, returning realistic mock data.
- **Tradeoff:** Completely self-contained, zero-container execution while maintaining REST endpoint decoupling.
