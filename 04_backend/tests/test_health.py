"""Teste do endpoint de healthcheck (BL-02)."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200_with_expected_shape():
    """`GET /health` deve responder 200 com status da API e do PostgreSQL."""
    response = client.get("/health")

    assert response.status_code == 200

    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert "app" in body
    assert body["database"] in {"ok", "unavailable"}
