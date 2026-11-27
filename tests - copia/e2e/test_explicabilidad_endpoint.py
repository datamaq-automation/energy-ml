"""tests/e2e/test_explicabilidad_endpoint.py — Tests del endpoint GET /api/v1/explain/tree."""

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_explain_tree_retorna_estructura_valida(client: TestClient) -> None:
    """GET /api/v1/explain/tree retorna árbol CART serializado con estructura válida."""
    response = client.get("/api/v1/explain/tree")
    assert response.status_code == 200

    data = response.json()

    assert data["tipo"] == "arbol_clasificador"
    assert isinstance(data["rasgos"], list)
    assert isinstance(data["clases"], list)
    assert data["profundidad"] >= 0
    assert data["hojas"] >= 1

    assert "raiz" in data
    assert data["raiz"]["tipo"] in ["decision", "hoja"]


def test_explain_tree_raiz_es_nodo_valido(client: TestClient) -> None:
    """GET /api/v1/explain/tree: la raíz es un nodo con estructura correcta."""
    response = client.get("/api/v1/explain/tree")
    assert response.status_code == 200

    raiz = response.json()["raiz"]

    assert "tipo" in raiz
    assert "muestras" in raiz
    assert "distribucion" in raiz

    if raiz["tipo"] == "decision":
        assert "rasgo" in raiz
        assert "threshold" in raiz
        assert "izquierda" in raiz
        assert "derecha" in raiz
    elif raiz["tipo"] == "hoja":
        assert "clase" in raiz


def test_explain_tree_hojas_tienen_clase_predicha(client: TestClient) -> None:
    """GET /api/v1/explain/tree: todas las hojas tienen clase predicha."""

    def verificar_hoja_recursiva(nodo: dict) -> None:
        if nodo["tipo"] == "hoja":
            assert "clase" in nodo
            assert nodo["clase"] is not None
        elif nodo["tipo"] == "decision":
            if nodo.get("izquierda"):
                verificar_hoja_recursiva(nodo["izquierda"])
            if nodo.get("derecha"):
                verificar_hoja_recursiva(nodo["derecha"])

    response = client.get("/api/v1/explain/tree")
    assert response.status_code == 200

    raiz = response.json()["raiz"]
    verificar_hoja_recursiva(raiz)
