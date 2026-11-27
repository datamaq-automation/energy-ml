"""tests/e2e/test_endpoint_mediciones.py — Tests del endpoint /mediciones/fuente."""

from pathlib import Path

from fastapi.testclient import TestClient

from src.infrastructure.settings.config import get_settings
from src.main import create_app


def test_mediciones_fuente_modo_local(tmp_path: Path, monkeypatch) -> None:
    """GET /api/v1/mediciones/fuente en modo local."""
    # Crear CSV dummy
    (tmp_path / "test.csv").write_text(
        "instante,potencia_kw\n2026-10-03T12:00:00,50.0\n", encoding="utf-8"
    )

    # Setear modo local
    monkeypatch.setenv("MEDICIONES_SOURCE", "local")
    monkeypatch.setenv("MEDICIONES_CSV_DIR", str(tmp_path))

    # Limpiar cache de settings
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/mediciones/fuente")

    assert response.status_code == 200
    data = response.json()
    assert data["fuente"] == "local"
    assert isinstance(data["medidores"], list)
    assert "test" in data["medidores"]
    assert data["ultima_descarga"] is None  # Local no tiene metadatos de descarga


def test_mediciones_fuente_endpoint_existe() -> None:
    """Endpoint existe en OpenAPI."""
    app = create_app()
    client = TestClient(app)

    # Verificar que está en el schema
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    # Buscar el endpoint
    paths = schema.get("paths", {})
    assert "/mediciones/fuente" in paths or "/api/v1/mediciones/fuente" in str(paths)
