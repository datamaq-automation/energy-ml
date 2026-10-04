"""tests/e2e/test_metricas_endpoint.py — Tests del endpoint GET /api/v1/metrics."""

import pytest
from fastapi.testclient import TestClient

from src.domain.cargas.entities import MatrizConfusion
from src.infrastructure.fastapi.dependencies import MatrizConfusionRepository
from src.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_metrics_endpoint_devuelve_metricas_vacias_inicialmente(client: TestClient) -> None:
    """GET /api/v1/metrics sin matriz registrada retorna exactitud 0."""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["exactitud_global"] == 0.0
    assert data["total_ejemplos"] == 0
    assert data["f1_macro"] == 0.0
    assert data["f1_ponderado"] == 0.0


def test_metrics_endpoint_calcula_exactitud_y_f1(client: TestClient) -> None:
    """GET /api/v1/metrics con matriz registrada calcula accuracy, F1 macro y ponderado."""
    # Registra matriz de confusión sintética
    clases = ["A", "B"]
    celdas = {
        "A": {"A": 80, "B": 20},  # 80 bien clasificados de A, 20 mal
        "B": {"A": 10, "B": 90},  # 10 mal de B, 90 bien
    }
    matriz = MatrizConfusion(clases=clases, celdas=celdas)

    # Inyecta en app.state
    app = client.app
    if not hasattr(app.state, "matriz_confusion_repo"):
        app.state.matriz_confusion_repo = MatrizConfusionRepository()
    app.state.matriz_confusion_repo.guardar(matriz)

    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()

    # Accuracy = (80 + 90) / 200 = 0.85
    assert abs(data["exactitud_global"] - 0.85) < 0.01
    assert data["total_ejemplos"] == 200

    # Verifica que hay métricas por clase
    assert len(data["metricas_por_clase"]) == 2

    # Clase A: precision = 80/(80+10) = 0.889, sensibilidad = 80/100 = 0.8
    clase_a = next(m for m in data["metricas_por_clase"] if m["clase"] == "A")
    assert abs(clase_a["precision"] - 0.8889) < 0.01
    assert abs(clase_a["sensibilidad"] - 0.8) < 0.01

    # Verifica F1 macro y ponderado > 0
    assert data["f1_macro"] > 0.0
    assert data["f1_ponderado"] > 0.0


def test_metrics_endpoint_matriz_confusión_perfecta(client: TestClient) -> None:
    """GET /api/v1/metrics con clasificación perfecta: exactitud=1, f1=1."""
    clases = ["X", "Y", "Z"]
    celdas = {
        "X": {"X": 50, "Y": 0, "Z": 0},
        "Y": {"X": 0, "Y": 40, "Z": 0},
        "Z": {"X": 0, "Y": 0, "Z": 60},
    }
    matriz = MatrizConfusion(clases=clases, celdas=celdas)

    app = client.app
    if not hasattr(app.state, "matriz_confusion_repo"):
        app.state.matriz_confusion_repo = MatrizConfusionRepository()
    app.state.matriz_confusion_repo.guardar(matriz)

    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()

    assert abs(data["exactitud_global"] - 1.0) < 0.001
    assert abs(data["f1_macro"] - 1.0) < 0.001
    assert abs(data["f1_ponderado"] - 1.0) < 0.001

    for metrica in data["metricas_por_clase"]:
        assert abs(metrica["f1"] - 1.0) < 0.001
