"""tests/unit/test_health_endpoint.py — Prueba unitaria canónica de endpoint."""

from __future__ import annotations


def test_health_endpoint_returns_ok(sync_client) -> None:
    response = sync_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data
