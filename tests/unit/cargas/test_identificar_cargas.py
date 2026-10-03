"""tests/unit/cargas/test_identificar_cargas.py — Caso de uso con repositorio y agrupador falsos."""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from src.application.cargas.dtos.identificar_cargas import IdentificarCargasRequest
from src.application.cargas.use_cases.identificar_cargas import IdentificarCargasUseCase
from src.domain.cargas.entities import EventoCarga, Medicion

T0 = datetime(2026, 9, 20)


class RepoFalso:
    def __init__(self, kw: list[float]) -> None:
        self.kw = kw

    def listar(self, medidor: str, desde: datetime, hasta: datetime) -> list[Medicion]:
        return [Medicion(T0 + timedelta(minutes=5 * i), p) for i, p in enumerate(self.kw)]


class AgrupadorPorSigno:
    def agrupar(self, eventos: list[EventoCarga]) -> list[int]:
        return [0 for _ in eventos]


def pedir(kw: list[float]) -> IdentificarCargasUseCase:
    return IdentificarCargasUseCase(RepoFalso(kw), AgrupadorPorSigno(), umbral_kw=60)


def test_identifica_una_carga_ciclica() -> None:
    req = IdentificarCargasRequest(medidor="Trafo arriba", desde=T0, hasta=T0 + timedelta(days=1))
    res = pedir([120, 210, 120, 211, 121]).execute(req)
    assert (res.mediciones, res.eventos) == (5, 4)
    assert res.potencia_media_kw == 156.4
    assert [(c.encendidos, c.apagados, c.ciclos) for c in res.cargas] == [(2, 2, 2)]


def test_sin_datos_devuelve_vacio() -> None:
    req = IdentificarCargasRequest(medidor="X", desde=T0, hasta=T0 + timedelta(hours=1))
    res = pedir([]).execute(req)
    assert (res.mediciones, res.eventos, res.cargas) == (0, 0, [])


def test_rango_invertido_es_invalido() -> None:
    with pytest.raises(ValidationError):
        IdentificarCargasRequest(medidor="X", desde=T0, hasta=T0)
