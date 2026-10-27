import json
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.main import app
from backend.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set up in‑memory SQLite for isolated tests
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Import models so their tables are registered with Base
from backend.models import investigation, evidence, correlation, graph  # noqa: F401
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply the dependency override
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_osint_route_success(monkeypatch):
    # Mock the service function to return deterministic data
    def fake_run_osint_lookup(investigation, target, target_type, db, registry=None):
        fake_evidence = {
            "id": 1,
            "investigation_id": investigation.id,
            "source_type": "osint",
            "source_name": "mockprovider",
            "source_url": "https://example.com",
            "title": "mockprovider: mock_finding",
            "content": "mockvalue",
            "evidence_type": "email",
            "confidence": 0.0,
            "collected_at": datetime.now(timezone.utc),
            "metadata_json": "{}",
            "normalised_value": "mockvalue",
        }
        provider_result = {
            "provider": "mockprovider",
            "status": "ok",
            "target": target,
            "target_type": target_type,
            "findings": [],
        }
        return (target, target_type, [provider_result], [fake_evidence])

    monkeypatch.setattr('backend.routes.osint.run_osint_lookup', fake_run_osint_lookup)

    # Create a dummy investigation via the API
    inv_resp = client.post("/api/investigations", json={"title": "Test", "description": "desc", "mode": "demo"})
    assert inv_resp.status_code == 201
    investigation_id = inv_resp.json()["id"]

    payload = {"target": "example.com", "target_type": "domain"}
    resp = client.post(f"/api/investigations/{investigation_id}/osint", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["investigation_id"] == investigation_id
    assert data["target"] == "example.com"
    assert data["evidence_created_count"] == 1
    assert isinstance(data["evidence_created"], list)

    # Clean up overrides after test
    app.dependency_overrides.clear()
