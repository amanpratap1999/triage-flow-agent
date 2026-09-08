import re
import json
import logging
from typing import Dict, Any, Tuple, Optional, List
import httpx
from src.config import settings
from src.tools import lookup_order, lookup_account, check_refund_eligibility

logger = logging.getLogger(__name__)

# High-risk keywords that trigger immediate human escalation
HOSTILE_KEYWORDS = [
    "lawyer", "attorney", "sue", "lawsuit", "legal action",
    "chargeback", "dispute with bank", "fraud", "scam",
    "police", "attorney general", "better business bureau", "bbb"
]

def detect_high_risk_sentiment(text: str) -> Optional[str]:
    lower = text.lower()
    for kw in HOSTILE_KEYWORDS:
        if kw in lower:
            return f"Detected high-risk legal/dispute signal: '{kw}'"
    return None

def extract_order_id(text: str) -> Optional[str]:
    m = re.search(r"\b(ORD-\d+)\b", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m2 = re.search(r"\border\s*(?:#|number|id)?\s*([A-Za-z0-9-]+)\b", text, re.IGNORECASE)
    if m2 and len(m2.group(1)) >= 3:
        cand = m2.group(1).upper()
        return cand if cand.startswith("ORD-") else f"ORD-{cand}"
    return None

def extract_email(text: str) -> Optional[str]:
    m = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
    return m.group(0).lower() if m else None

class TriageResult:
    def __init__(
        self,
        category: str,
        status: str,  # 'resolved' or 'escalated'
        confidence: float,
        resolution_text: Optional[str] = None,
        escalation_reason: Optional[str] = None,
        recommended_action: Optional[str] = None,
        tool_traces: Optional[List[Dict[str, Any]]] = None
    ):
        self.category = category
        self.status = status
        self.confidence = confidence
        self.resolution_text = resolution_text
        self.escalation_reason = escalation_reason
        self.recommended_action = recommended_action
        self.tool_traces = tool_traces or []

async def run_triage_pipeline(customer_email: str, subject: str, body: str) -> TriageResult:
    full_text = f"{subject}\n{body}"
    lower_text = full_text.lower()
    tool_traces: List[Dict[str, Any]] = []

    # 1. Check for High-Risk Escalation Triggers
    risk_signal = detect_high_risk_sentiment(full_text)
    if risk_signal:
        return TriageResult(
            category="legal_and_fraud_dispute",
            status="escalated",
            confidence=0.98,
            escalation_reason=f"Priority Escalation: {risk_signal}. Requires immediate human supervisor intervention.",
            recommended_action="Route to Senior Customer Relations & Legal Compliance Queue",
            tool_traces=[]
        )

    # 2. Extract Entities
    order_id = extract_order_id(full_text)
    email = extract_email(full_text) or customer_email

    # 3. Classify Intent & Execute Tools

    # Check for delivery disputes / missing items / wrong address
    if any(k in lower_text for k in ["missing", "half of my items", "partial", "wrong address", "wrong street", "never arrived", "not received", "didn't receive", "delivered to wrong"]):
        return TriageResult(
            category="delivery_dispute",
            status="escalated",
            confidence=0.92,
            escalation_reason=f"Customer reports delivery anomaly (missing items or wrong address) for {order_id or 'unknown order'}.",
            recommended_action="Initiate warehouse audit or carrier misdelivery claim.",
            tool_traces=[]
        )

    # Check for urgent shipment cancellation
    if any(k in lower_text for k in ["cancel shipment", "stop shipment", "recall", "stop the truck"]):
        return TriageResult(
            category="order_cancellation",
            status="escalated",
            confidence=0.92,
            escalation_reason=f"Customer requested urgent shipment cancellation / carrier intercept for {order_id or 'unknown order'}.",
            recommended_action="Attempt carrier intercept via FedEx/UPS portal or alert logistics dispatch.",
            tool_traces=[]
        )

    # --- CATEGORY A: ORDER TRACKING & LOGISTICS ---
    is_order_inquiry = any(k in lower_text for k in [
        "order", "ord-", "track", "tracking", "package", "delivery", "shipped",
        "shipping", "status of", "where is", "where order", "has arrived"
    ]) and not any(k in lower_text for k in ["refund", "return", "cancel order", "money back"])

    if is_order_inquiry:
        if not order_id:
            # Ambiguous: missing order ID
            return TriageResult(
                category="order_inquiry",
                status="escalated",
                confidence=0.65,
                escalation_reason="Customer is inquiring about order tracking, but provided no valid Order ID.",
                recommended_action="Send templated response requesting customer Order ID and zip code.",
                tool_traces=[]
            )

        # Call Tool
        order_data = lookup_order(order_id)
        tool_traces.append({
            "tool_name": "lookup_order",
            "tool_input": json.dumps({"order_id": order_id}),
            "tool_output": json.dumps(order_data)
        })

        if not order_data["success"]:
            return TriageResult(
                category="order_inquiry",
                status="escalated",
                confidence=0.70,
                escalation_reason=f"Order {order_id} could not be located in the warehouse fulfillment system.",
                recommended_action="Verify customer purchase details in secondary legacy billing database.",
                tool_traces=tool_traces
            )

        ord_info = order_data["order"]
        if ord_info["status"] == "in_transit":
            resolution = (
                f"Hello! Your order ({order_id}) is currently in transit via {ord_info['carrier']} "
                f"under tracking number {ord_info['tracking_number']}. "
                f"Estimated delivery is scheduled for {ord_info['estimated_delivery']}."
            )
            return TriageResult(
                category="order_inquiry",
                status="resolved",
                confidence=0.95,
                resolution_text=resolution,
                tool_traces=tool_traces
            )
        elif ord_info["status"] == "delivered":
            resolution = (
                f"Hello! Our records indicate that your order ({order_id}) was successfully delivered "
                f"via {ord_info['carrier']} ({ord_info.get('delivered_date', 'recently')}). "
                f"Please check your front porch, parcel locker, or building reception desk."
            )
            return TriageResult(
                category="order_inquiry",
                status="resolved",
                confidence=0.92,
                resolution_text=resolution,
                tool_traces=tool_traces
            )
        elif "delayed" in ord_info["status"]:
            resolution = (
                f"Hello! Your order ({order_id}) is currently experiencing a shipment delay: {ord_info['estimated_delivery']}. "
                f"Your tracking number with {ord_info['carrier']} is {ord_info['tracking_number']}."
            )
            return TriageResult(
                category="order_inquiry",
                status="resolved",
                confidence=0.90,
                resolution_text=resolution,
                tool_traces=tool_traces
            )

    # --- CATEGORY B: REFUND & RETURN REQUESTS ---
    if any(k in lower_text for k in ["refund", "return", "money back", "cancel order", "defective", "broken"]):
        if not order_id:
            return TriageResult(
                category="refund_request",
                status="escalated",
                confidence=0.60,
                escalation_reason="Customer requested refund/return without specifying an Order ID.",
                recommended_action="Request Order ID and purchase receipt from customer.",
                tool_traces=[]
            )

        # Check for ambiguous timing in text
        days_override = None
        if "two months" in lower_text or "2 months" in lower_text or "60 days" in lower_text:
            days_override = 60
        elif "45 days" in lower_text:
            days_override = 45

        refund_check = check_refund_eligibility(order_id, days_since_purchase=days_override)
        tool_traces.append({
            "tool_name": "check_refund_eligibility",
            "tool_input": json.dumps({"order_id": order_id, "days_override": days_override}),
            "tool_output": json.dumps(refund_check)
        })

        if refund_check["eligible"]:
            resolution = (
                f"Your refund request for order {order_id} has been approved in accordance with our "
                f"30-day customer satisfaction guarantee. A pre-paid return label has been emailed to you, "
                f"and your original payment method will be credited upon warehouse receipt."
            )
            return TriageResult(
                category="refund_request",
                status="resolved",
                confidence=0.92,
                resolution_text=resolution,
                tool_traces=tool_traces
            )
        else:
            return TriageResult(
                category="refund_request",
                status="escalated",
                confidence=0.88,
                escalation_reason=f"Policy Exception: {refund_check['policy_rule']}",
                recommended_action="Manager review required: determine whether to issue a one-time store credit courtesy.",
                tool_traces=tool_traces
            )

    # --- CATEGORY C: ACCOUNT SECURITY & ACCESS ---
    if any(k in lower_text for k in ["locked out", "unlock account", "password reset", "can't log in", "cannot login", "login failed", "2fa"]):
        account_data = lookup_account(email)
        tool_traces.append({
            "tool_name": "lookup_account",
            "tool_input": json.dumps({"email": email}),
            "tool_output": json.dumps(account_data)
        })

        acc = account_data.get("account", {})
        if acc.get("status") == "under_fraud_review":
            return TriageResult(
                category="account_access",
                status="escalated",
                confidence=0.95,
                escalation_reason="Account is under active security fraud review for unauthorized geo-IP access.",
                recommended_action="Forward to Trust & Safety team for identity verification verification.",
                tool_traces=tool_traces
            )

        resolution = (
            f"We have verified your account ({email}). A secure one-time password reset link "
            f"and temporary unlock key have been sent to your registered email address. "
            f"This link remains valid for 15 minutes."
        )
        return TriageResult(
            category="account_access",
            status="resolved",
            confidence=0.90,
            resolution_text=resolution,
            tool_traces=tool_traces
        )

    # --- CATEGORY D: OUT-OF-SCOPE / COMPLEX / AMBIGUOUS ---
    return TriageResult(
        category="general_inquiry",
        status="escalated",
        confidence=0.55,
        escalation_reason="Unrecognized inquiry or multi-topic request that falls outside autonomous triage policies.",
        recommended_action="Assign to General Support Tier-1 agent for personalized response.",
        tool_traces=[]
    )
