"""tests/e2e/test_identify_loads.py — Endpoint /identify-loads con dependencias sustituidas."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from src.application.cargas.use_cases.identificar_cargas import IdentificarCargasUseCase
from src.domain.cargas.entities import EventoCarga, Medicion
from src.infrastructure.fastapi.dependencies import get_identificar_cargas
from src.infrastructure.settings.logger import logger
from src.main import app

T0 = datetime(2026, 9, 20)


class RepoFalso:
    def listar(self, medidor: str, desde: datetime, hasta: datetime) -> list[Medicion]:
        return [Medicion(T0 + timedelta(minutes=5 * i), p) for i, p in enumerate([120, 210, 120])]


class AgrupadorUnico:
    def agrupar(self, eventos: list[EventoCarga]) -> list[int]:
        return [0] * len(eventos)


def test_identify_loads_devuelve_cargas() -> None:
    app.dependency_overrides[get_identificar_cargas] = lambda: IdentificarCargasUseCase(
        RepoFalso(), AgrupadorUnico(), umbral_kw=60, logger=logger
    )
    try:
        r = TestClient(app).get(
            "/api/v1/identify-loads",
            params={"medidor": "Trafo arriba", "desde": "2026-09-20T00:00", "hasta": "2026-09-21T00:00"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["eventos"] == 2
        assert body["cargas"] == [{"potencia_tipica_kw": 90.0, "encendidos": 1, "apagados": 1, "ciclos": 1}]
        assert body["umbral"] == {"kw": 60.0, "automatico": False, "separacion": None, "confiable": None}
        assert sum(b["cantidad"] for b in body["histograma"]) == 2
        invalido = TestClient(app).get(
            "/api/v1/identify-loads", params={"medidor": "X", "desde": "2026-09-21", "hasta": "2026-09-20"}
        )
        assert invalido.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_raiz_sirve_la_vista_de_energia() -> None:
    r = TestClient(app).get("/")
    assert r.status_code == 200
    assert "Identificador de Cargas" in r.text



def test_static_sirve_css_y_js() -> None:
    cliente = TestClient(app)
    assert cliente.get("/static/energia.css").status_code == 200
    assert cliente.get("/static/energia.js").status_code == 200
