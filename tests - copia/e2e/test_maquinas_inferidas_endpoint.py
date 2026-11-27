"""tests/e2e/test_maquinas_inferidas_endpoint.py — E2E tests for máquinas inferidas endpoint."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.cache.maquinas_cache import MaquinasCacheMemoria
from src.main import app


@pytest.fixture
def client():
    """Test client para FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_cache():
    """Setup cache con datos de test antes de cada test."""
    cache = MaquinasCacheMemoria()

    # Datos de ejemplo para planta_2_a
    cache.guardar(
        "planta_2_a",
        {
            "maquinas_inferidas": [
                {
                    "id": "carga_001",
                    "nombre": "Bomba A",
                    "potencia_tipica_kw": 92.5,
                    "encendidos": 412,
                    "apagados": 380,
                    "ciclos": 380,
                    "ciclos_por_dia": 24.5,
                    "dispersion_kw": 1.5,
                    "timestamp_analisis": "2026-10-05T03:30:00",
                    "fuente": "NILM-DBSCAN",
                }
            ],
            "actualizado_en": "2026-10-05T03:30:00",
        },
    )

    # Datos para planta_2_b (confianza media)
    cache.guardar(
        "planta_2_b",
        {
            "maquinas_inferidas": [
                {
                    "id": "carga_002",
                    "nombre": "Compresor B",
                    "potencia_tipica_kw": 45.0,
                    "encendidos": 198,
                    "apagados": 195,
                    "ciclos": 195,
                    "ciclos_por_dia": 12.1,
                    "dispersion_kw": 4.5,
                    "timestamp_analisis": "2026-10-05T03:30:00",
                    "fuente": "NILM-DBSCAN",
                }
            ],
            "actualizado_en": "2026-10-05T03:30:00",
        },
    )

    # Inyectar cache en app.state
    app.state.maquinas_cache = cache

    yield cache


class TestMaquinasInferidasEndpoint:
    """Tests para GET /api/v1/dispositivos/{id}/maquinas/inferidas."""

    def test_obtener_maquinas_inferidas_valido(self, client):
        """Endpoint retorna 200 con maquinas inferidas."""
        response = client.get("/api/v1/dispositivos/planta_2_a/maquinas/inferidas")

        assert response.status_code == 200
        data = response.json()
        assert data["dispositivo_id"] == "planta_2_a"
        assert len(data["maquinas_inferidas"]) == 1

    def test_respuesta_schema_correcto(self, client):
        """Respuesta cumple el schema esperado."""
        response = client.get("/api/v1/dispositivos/planta_2_a/maquinas/inferidas")

        assert response.status_code == 200
        data = response.json()

        # Validar estructura
        assert "dispositivo_id" in data
        assert "maquinas_inferidas" in data
        assert "actualizado_en" in data

        # Validar máquina
        maquina = data["maquinas_inferidas"][0]
        assert maquina["id"] == "carga_001"
        assert maquina["nombre"] == "Bomba A"
        assert maquina["potencia_tipica_kw"] == 92.5
        assert maquina["confianza"] == "alta"
        assert maquina["encendidos"] == 412
        assert maquina["apagados"] == 380
        assert maquina["ciclos_por_dia"] == 24.5
        assert maquina["dispersion_kw"] == 1.5
        assert maquina["fuente"] == "NILM-DBSCAN"

    def test_confianza_media_calculada(self, client):
        """Confianza se calcula correctamente (media)."""
        response = client.get("/api/v1/dispositivos/planta_2_b/maquinas/inferidas")

        assert response.status_code == 200
        maquina = response.json()["maquinas_inferidas"][0]
        assert maquina["confianza"] == "media"

    def test_dispositivo_no_encontrado_404(self, client):
        """404 si dispositivo no tiene datos en cache."""
        response = client.get("/api/v1/dispositivos/dispositivo_inexistente/maquinas/inferidas")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_timestamp_analisis_iso8601(self, client):
        """Timestamp del análisis está en ISO 8601."""
        response = client.get("/api/v1/dispositivos/planta_2_a/maquinas/inferidas")

        maquina = response.json()["maquinas_inferidas"][0]
        # Debe poder parsearse como datetime
        timestamp = datetime.fromisoformat(maquina["timestamp_analisis"])
        assert timestamp.year == 2026

    def test_cache_persiste_entre_requests(self, client):
        """Cache persiste entre múltiples requests."""
        # Primer request
        response1 = client.get("/api/v1/dispositivos/planta_2_a/maquinas/inferidas")
        assert response1.status_code == 200

        # Segundo request - debe usar el mismo cache
        response2 = client.get("/api/v1/dispositivos/planta_2_a/maquinas/inferidas")
        assert response2.status_code == 200
        assert response1.json() == response2.json()

    def test_multiples_dispositivos(self, client):
        """Endpoint responde correctamente para múltiples dispositivos."""
        # planta_2_a
        r1 = client.get("/api/v1/dispositivos/planta_2_a/maquinas/inferidas")
        assert r1.status_code == 200
        assert r1.json()["dispositivo_id"] == "planta_2_a"

        # planta_2_b
        r2 = client.get("/api/v1/dispositivos/planta_2_b/maquinas/inferidas")
        assert r2.status_code == 200
        assert r2.json()["dispositivo_id"] == "planta_2_b"

        # Datos son diferentes
        assert r1.json() != r2.json()

    def test_lista_vacia_valida(self, client, setup_cache):
        """Si no hay máquinas, retorna lista vacía (válido)."""
        cache = setup_cache
        cache.guardar(
            "planta_vacia",
            {
                "maquinas_inferidas": [],
                "actualizado_en": "2026-10-05T03:30:00",
            },
        )

        response = client.get("/api/v1/dispositivos/planta_vacia/maquinas/inferidas")

        assert response.status_code == 200
        assert response.json()["maquinas_inferidas"] == []

    def test_endpoint_openapi_documentado(self, client):
        """Endpoint aparece en OpenAPI."""
        response = client.get("/api/v1/openapi.json")

        assert response.status_code == 200
        spec = response.json()

        # Buscar el endpoint
        paths = spec.get("paths", {})
        dispositivos_path = None
        for path in paths:
            if "dispositivos" in path and "maquinas/inferidas" in path:
                dispositivos_path = path
                break

        assert dispositivos_path is not None
        assert "get" in paths[dispositivos_path]
