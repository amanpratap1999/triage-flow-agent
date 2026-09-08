import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.database import Base, get_db
from src.main import app

# In-memory SQLite for testing with StaticPool
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "sqlite" in data["database"]

def test_routine_order_status_resolves(client):
    payload = {
        "customer_email": "jane@example.com",
        "subject": "Status of order ORD-101",
        "body": "Hello, can you tell me where order ORD-101 is right now?"
    }
    res = client.post("/tickets", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "resolved"
    assert data["confidence"] >= 0.80
    assert "in transit" in data["resolution_text"].lower()
    assert "fedex" in data["resolution_text"].lower()
    assert len(data["tool_executions"]) >= 1

def test_missing_order_id_escalates(client):
    payload = {
        "customer_email": "mark@example.com",
        "subject": "Where is my package?",
        "body": "I ordered a desk last week and haven't received it yet."
    }
    res = client.post("/tickets", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "escalated"
    assert "order id" in data["escalation_reason"].lower()

def test_out_of_policy_refund_escalates(client):
    payload = {
        "customer_email": "sam@example.com",
        "subject": "Return request for ORD-103",
        "body": "I want to return ORD-103 because I don't need it anymore."
    }
    res = client.post("/tickets", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "escalated"
    assert "policy" in data["escalation_reason"].lower()
    assert "manager" in data["recommended_action"].lower()

def test_legal_threat_escalates_immediately(client):
    payload = {
        "customer_email": "angry@example.com",
        "subject": "Filing a lawsuit against your company",
        "body": "I will contact my attorney and sue your company for damages if this isn't handled!"
    }
    res = client.post("/tickets", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "escalated"
    assert data["category"] == "legal_and_fraud_dispute"
    assert "legal" in data["escalation_reason"].lower()

def test_human_escalation_action(client):
    # Create an escalated ticket
    create_res = client.post("/tickets", json={
        "customer_email": "ambiguous@example.com",
        "subject": "Confusing question",
        "body": "I need help with multiple items on different accounts."
    })
    ticket_id = create_res.json()["id"]
    assert create_res.json()["status"] == "escalated"

    # Human supervisor approves exception
    action_res = client.post(f"/tickets/{ticket_id}/action", json={
        "action": "approve_resolution",
        "notes": "Supervisor approved one-time goodwill resolution."
    })
    assert action_res.status_code == 200
    data = action_res.json()
    assert data["status"] == "resolved"
    assert data["human_action"] == "approve_resolution"
    assert "supervisor approved" in data["resolution_text"].lower()
