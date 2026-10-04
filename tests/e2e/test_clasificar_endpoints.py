"""tests/e2e/test_clasificar_endpoints.py — Pruebas e2e de los endpoints de clasificación Bayes y k-NN."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.settings.config import get_settings
from src.main import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("MODELOS_DIR", str(tmp_path / "models"))
    get_settings.cache_clear()
    with TestClient(create_app()) as c:
        yield c
    get_settings.cache_clear()


def test_lifespan_carga_modelos_en_app_state(client: TestClient, tmp_path: Path) -> None:
    modelos = client.app.state.modelos  # type: ignore[attr-defined]
    assert set(modelos.keys()) == {"bayes", "knn"}
    assert (tmp_path / "models" / "bayes.joblib").exists()
    assert (tmp_path / "models" / "knn.joblib").exists()


def test_classify_bayes_normal(client: TestClient) -> None:
    r = client.post(
        "/api/v1/classify/bayes",
        json={
            "potencia_kva": 400.0,
            "temperatura_aceite_c": 55.0,
            "temperatura_devanados_c": 65.0,
            "corriente_a": 320.0,
        },
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["estado"] == "NORMAL"
    assert cuerpo["es_contingencia"] is False
    assert abs(sum(cuerpo["probabilidades"].values()) - 1.0) < 0.01


def test_classify_bayes_critica(client: TestClient) -> None:
    r = client.post(
        "/api/v1/classify/bayes",
        json={
            "potencia_kva": 950.0,
            "temperatura_aceite_c": 105.0,
            "temperatura_devanados_c": 125.0,
            "corriente_a": 900.0,
        },
    )
    assert r.status_code == 200
    assert r.json()["estado"] == "CRITICA"
    assert r.json()["es_contingencia"] is True


def test_classify_bayes_rechaza_campos_extra_y_negativos(client: TestClient) -> None:
    base = {
        "potencia_kva": 400.0,
        "temperatura_aceite_c": 55.0,
        "temperatura_devanados_c": 65.0,
        "corriente_a": 320.0,
    }
    assert client.post("/api/v1/classify/bayes", json={**base, "extra": 1}).status_code == 422
    assert (
        client.post("/api/v1/classify/bayes", json={**base, "potencia_kva": -1}).status_code == 422
    )


def test_classify_knn_led(client: TestClient) -> None:
    r = client.post(
        "/api/v1/classify/knn",
        json={
            "potencia_activa_kw": 6.0,
            "potencia_reactiva_kvar": 0.5,
            "thd_corriente": 20.0,
            "factor_desbalance": 1.0,
            "k": 5,
        },
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["clase_predicha"] == "ILUMINACION_LED"
    assert len(cuerpo["vecinos"]) == 5
    assert 0.0 <= cuerpo["confianza"] <= 1.0


def test_classify_knn_manhattan(client: TestClient) -> None:
    r = client.post(
        "/api/v1/classify/knn",
        json={
            "potencia_activa_kw": 50.0,
            "potencia_reactiva_kvar": 0.6,
            "thd_corriente": 1.5,
            "k": 3,
            "metrica": "manhattan",
        },
    )
    assert r.status_code == 200
    assert r.json()["clase_predicha"] == "RESISTENCIA_TERMICA"


def test_classify_knn_rechaza_k_invalido(client: TestClient) -> None:
    r = client.post(
        "/api/v1/classify/knn",
        json={
            "potencia_activa_kw": 6.0,
            "potencia_reactiva_kvar": 0.5,
            "thd_corriente": 20.0,
            "k": 0,
        },
    )
    assert r.status_code == 422
