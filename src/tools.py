import re
from typing import Dict, Any, Optional

MOCK_ORDERS: Dict[str, Dict[str, Any]] = {
    "ORD-101": {
        "order_id": "ORD-101",
        "status": "in_transit",
        "carrier": "FedEx",
        "tracking_number": "FX-884920194",
        "estimated_delivery": "Tomorrow by 5:00 PM",
        "items": ["Ergonomic Mechanical Keyboard"],
        "days_since_purchase": 3,
        "amount": 129.99
    },
    "ORD-102": {
        "order_id": "ORD-102",
        "status": "delivered",
        "carrier": "UPS",
        "tracking_number": "UPS-499201928",
        "delivered_date": "Yesterday, left at front door",
        "items": ["UltraWide 34-inch Monitor"],
        "days_since_purchase": 5,
        "amount": 499.00
    },
    "ORD-103": {
        "order_id": "ORD-103",
        "status": "delivered",
        "carrier": "USPS",
        "tracking_number": "940011189922",
        "delivered_date": "45 days ago",
        "items": ["Wireless Noise-Cancelling Headphones"],
        "days_since_purchase": 45,
        "amount": 199.50
    },
    "ORD-104": {
        "order_id": "ORD-104",
        "status": "delayed_weather",
        "carrier": "FedEx",
        "tracking_number": "FX-992018821",
        "estimated_delivery": "Pending weather clearance in Memphis hub",
        "items": ["Smart Standing Desk"],
        "days_since_purchase": 6,
        "amount": 650.00
    }
}

MOCK_ACCOUNTS: Dict[str, Dict[str, Any]] = {
    "alice@example.com": {
        "email": "alice@example.com",
        "account_id": "ACC-501",
        "status": "locked_temporary",
        "lock_reason": "Too many failed password attempts",
        "mfa_enabled": True,
        "tier": "Enterprise"
    },
    "bob@example.com": {
        "email": "bob@example.com",
        "account_id": "ACC-502",
        "status": "active",
        "lock_reason": None,
        "mfa_enabled": True,
        "tier": "Standard"
    },
    "eve@suspicious.org": {
        "email": "eve@suspicious.org",
        "account_id": "ACC-999",
        "status": "under_fraud_review",
        "lock_reason": "Suspicious login from unauthorized geo-IP",
        "mfa_enabled": False,
        "tier": "Standard"
    }
}

def lookup_order(order_id: str) -> Dict[str, Any]:
    """
    Mock stub tool: Retrieves current order logistics, shipping, and delivery details.
    """
    clean_id = order_id.upper().strip()
    if clean_id in MOCK_ORDERS:
        return {"success": True, "order": MOCK_ORDERS[clean_id]}
    
    # Generate realistic dynamic response for synthetic ORD-XXXX IDs
    if re.match(r"^ORD-\d+$", clean_id):
        return {
            "success": True,
            "order": {
                "order_id": clean_id,
                "status": "in_transit",
                "carrier": "UPS",
                "tracking_number": f"1Z9999999{clean_id[-3:]}",
                "estimated_delivery": "In 2 business days",
                "items": ["Standard Retail Merchandise"],
                "days_since_purchase": 4,
                "amount": 79.99
            }
        }
        
    return {"success": False, "error": f"Order ID '{order_id}' not found in fulfillment database"}

def lookup_account(email: str) -> Dict[str, Any]:
    """
    Mock stub tool: Looks up customer account security and subscription status.
    """
    clean_email = email.lower().strip()
    if clean_email in MOCK_ACCOUNTS:
        return {"success": True, "account": MOCK_ACCOUNTS[clean_email]}
        
    # Default active account for test emails
    return {
        "success": True,
        "account": {
            "email": clean_email,
            "account_id": f"ACC-{abs(hash(clean_email)) % 10000}",
            "status": "active",
            "lock_reason": None,
            "mfa_enabled": True,
            "tier": "Standard"
        }
    }

def check_refund_eligibility(order_id: str, days_since_purchase: Optional[int] = None) -> Dict[str, Any]:
    """
    Mock stub tool: Evaluates company return policy (30-day window limit).
    """
    order_res = lookup_order(order_id)
    if not order_res["success"]:
        return {"eligible": False, "reason": f"Cannot verify refund: {order_res['error']}"}

    days = days_since_purchase if days_since_purchase is not None else order_res["order"].get("days_since_purchase", 0)
    amount = order_res["order"].get("amount", 0.0)

    if days <= 30:
        return {
            "eligible": True,
            "order_id": order_id,
            "days_since_purchase": days,
            "max_refund_amount": amount,
            "policy_rule": "Within standard 30-day return policy. Pre-paid return label issued."
        }
    else:
        return {
            "eligible": False,
            "order_id": order_id,
            "days_since_purchase": days,
            "policy_rule": f"Order was placed {days} days ago, exceeding the strict 30-day customer return policy."
        }
