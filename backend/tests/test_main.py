import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_vendor_intake():
    response = client.post("/api/v1/vendor/intake", json={
        "legal_name": "Test Corp",
        "jurisdiction": "US",
        "registration_number": "12345"
    })
    assert response.status_code == 200
    assert "input_id" in response.json()

def test_vendor_intake_missing_field():
    response = client.post("/api/v1/vendor/intake", json={
        "jurisdiction": "US"
        # Missing legal_name
    })
    assert response.status_code == 422  # Validation error
