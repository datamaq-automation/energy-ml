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
    def agrupar(self, eventos: list[EventoCarga], radio_kw: float, min_eventos: int) -> list[int]:
        return [0] * len(eventos)


def test_identify_loads_devuelve_cargas() -> None:
    app.dependency_overrides[get_identificar_cargas] = lambda: IdentificarCargasUseCase(
        RepoFalso(), AgrupadorUnico(), umbral_kw=60, logger=logger
    )
    try:
        r = TestClient(app).get(
            "/api/v1/identify-loads",
            params={
                "medidor": "Trafo arriba",
                "desde": "2026-09-20T00:00",
                "hasta": "2026-09-21T00:00",
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["eventos"] == 2
        assert body["cargas"] == [
            {
                "potencia_tipica_kw": 90.0,
                "encendidos": 1,
                "apagados": 1,
                "ciclos": 1,
                "ciclos_por_dia": None,
                "on_off": True,
                "dispersion_kw": 0.0,
            }
        ]
        assert body["umbral"] == {
            "kw": 60.0,
            "automatico": False,
            "separacion": None,
            "confiable": None,
        }
        assert sum(b["cantidad"] for b in body["histograma"]) == 2
        assert (body["encendidos"], body["apagados"], body["eventos_sin_grupo"]) == (1, 1, 0)
        assert [p["potencia_kw"] for p in body["serie"]] == [120, 210, 120]
        assert [(e["delta_kw"], e["carga_kw"]) for e in body["detalle_eventos"]] == [
            (90.0, 90.0),
            (-90.0, 90.0),
        ]
        invalido = TestClient(app).get(
            "/api/v1/identify-loads",
            params={"medidor": "X", "desde": "2026-09-21", "hasta": "2026-09-20"},
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


def test_guia_sirve_el_cuaderno_y_no_la_guia_docente() -> None:
    cliente = TestClient(app)
    assert "guia.js" in cliente.get("/guia").text
    md = cliente.get("/guia/cuaderno-alumno.md")
    assert md.status_code == 200
    assert md.headers["content-type"].startswith("text/markdown")
    assert md.text.startswith("# Cuaderno de trabajo")
    assert cliente.get("/guia/guia-docente.md").status_code == 404  # tiene las respuestas
    assert cliente.get("/guia/srs-spec-backend-fastapi.md").status_code == 404
