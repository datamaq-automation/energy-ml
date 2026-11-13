"""Pruebas end-to-end de la API SIBO con una base SQLite temporal."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sibo.infrastructure.fastapi.app import create_app


@pytest.fixture
def cliente(tmp_path: Path) -> Generator[TestClient, None, None]:
    app = create_app(tmp_path / "api-test.db")
    with TestClient(app) as test_client:
        yield test_client


def _registrar(cliente: TestClient, alimento_id: int = 1) -> dict[str, object]:
    respuesta = cliente.post(
        "/api/sibo/registros",
        json={
            "alimento_id": alimento_id,
            "porcion_g": 120,
            "fecha_hora": "2026-11-07T12:30:00",
            "sintomas": 4,
            "notas": "almuerzo de prueba",
        },
    )
    assert respuesta.status_code == 201
    return respuesta.json()


def test_salud_y_alimentos(cliente: TestClient) -> None:
    salud = cliente.get("/api/sibo/salud")
    assert salud.status_code == 200
    assert salud.json()["status"] == "ok"

    alimentos = cliente.get("/api/sibo/alimentos")
    assert alimentos.status_code == 200
    assert len(alimentos.json()) >= 40


def test_flujo_de_registro_y_eliminacion(cliente: TestClient) -> None:
    creado = _registrar(cliente)
    assert creado["alimento_nombre"]
    assert creado["id"] > 0

    listado = cliente.get("/api/sibo/registros")
    assert listado.status_code == 200
    assert len(listado.json()) == 1

    eliminado = cliente.delete(f"/api/sibo/registros/{creado['id']}")
    assert eliminado.status_code == 204
    assert cliente.get("/api/sibo/registros").json() == []


def test_registro_con_alimento_inexistente_devuelve_404(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/api/sibo/registros",
        json={"alimento_id": 9999, "porcion_g": 100, "sintomas": 0},
    )
    assert respuesta.status_code == 404


def test_serie_de_gases_por_dia_semana_y_mes(cliente: TestClient) -> None:
    _registrar(cliente)

    dia = cliente.get("/api/sibo/gases", params={"rango": "dia", "fecha": "2026-11-07"})
    assert dia.status_code == 200
    cuerpo = dia.json()
    assert cuerpo["rango"] == "dia"
    assert cuerpo["pico"] > 5
    assert len(cuerpo["puntos"]) == 25
    assert all(0 <= punto["nivel_estimado"] <= 100 for punto in cuerpo["puntos"])

    semana = cliente.get("/api/sibo/gases", params={"rango": "semana", "fecha": "2026-11-07"})
    assert semana.status_code == 200
    assert semana.json()["pico"] > 5

    mes = cliente.get("/api/sibo/gases", params={"rango": "mes", "fecha": "2026-11-07"})
    assert mes.status_code == 200
    assert len(mes.json()["puntos"]) == 31


def test_rango_invalido_devuelve_422(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/sibo/gases", params={"rango": "anio"})
    assert respuesta.status_code == 422


def test_recomendaciones_priorizan_bajo_fodmap(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/sibo/recomendaciones", params={"limite": 5})
    assert respuesta.status_code == 200
    recomendaciones = respuesta.json()
    assert len(recomendaciones) == 5
    assert recomendaciones[0]["alimento"]["fodmap"] != "alto"
    assert recomendaciones[0]["puntaje"] >= recomendaciones[-1]["puntaje"]
    assert recomendaciones[0]["motivo"]
