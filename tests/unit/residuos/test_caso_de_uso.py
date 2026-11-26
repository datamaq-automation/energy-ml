"""tests/unit/residuos/test_caso_de_uso.py — Caso de uso, controlador, presentador y reglas con dobles."""

from __future__ import annotations

from datetime import datetime

import pytest

from src.adapters.residuos.controllers.residuos_controller import ResiduosController
from src.adapters.residuos.presenters.residuos_presenter import ResiduosPresenter
from src.application.residuos.use_cases.pronosticar_residuos import PronosticarResiduosUseCase
from src.domain.residuos.exceptions import SerieCortaError
from src.domain.residuos.repositories import PronosticadorResiduos, RepositorioResiduos
from src.domain.residuos.services import (
    elegir_mejor_modelo,
    origenes_de_validacion,
    pronostico_persistencia,
)
from src.domain.residuos.value_objects import (
    MODELOS,
    MetricaValidacion,
    Pronostico,
    TotalMensual,
)


class RepositorioFalso(RepositorioResiduos):
    def __init__(self) -> None:
        self.guardados = 0

    def cargar(self) -> list[float]:
        return [100.0, 110.0, 120.0]

    def guardar(
        self,
        serie: list[TotalMensual],
        metricas: list[MetricaValidacion],
        pronosticos: list[Pronostico],
    ) -> list[str]:
        self.guardados += 1
        return ["serie.csv", "metricas.csv", "pronostico.csv"]


class PronosticadorFalso(PronosticadorResiduos):
    def serie_mensual(self, datos: list[float]) -> list[TotalMensual]:
        return [TotalMensual(f"2026-0{i + 1}", valor) for i, valor in enumerate(datos)]

    def validar(self, datos: list[float]) -> list[MetricaValidacion]:
        return [
            MetricaValidacion(modelo, "completo", mae, mae * 1.2, 12)
            for modelo, mae in zip(MODELOS, (664.0, 500.0, 381.7), strict=True)
        ] + [MetricaValidacion(MODELOS[0], "1 mes(es)", 10.0, 12.0, 4)]

    def pronosticar(self, datos: list[float]) -> list[Pronostico]:
        return [Pronostico(f"2026-{m:02d}", modelo, 1.0) for m in (4, 5, 6) for modelo in MODELOS]


@pytest.mark.parametrize("guardar", [True, False])
def test_controlador_corre_las_tres_etapas(guardar: bool) -> None:
    repositorio = RepositorioFalso()
    controlador = ResiduosController(
        PronosticarResiduosUseCase(repositorio, PronosticadorFalso()), ResiduosPresenter()
    )

    respuesta, lineas = controlador.pronosticar(guardar, datetime(2026, 11, 25, 8, 0))

    assert respuesta.id_informe == "residuos-20261125T080000"
    assert (respuesta.meses, respuesta.primer_mes, respuesta.ultimo_mes) == (
        3,
        "2026-01",
        "2026-03",
    )
    assert respuesta.mejor_modelo == "Bosque aleatorio"
    assert repositorio.guardados == int(guardar)
    assert len(respuesta.archivos) == 3 * int(guardar)
    assert len(respuesta.eventos) == 3
    assert sum(linea.startswith("  2026-0") for linea in lineas) == 3


def test_reglas_de_dominio() -> None:
    assert origenes_de_validacion(111) == [99, 102, 105, 108]
    with pytest.raises(SerieCortaError, match="demasiado corta"):
        origenes_de_validacion(24)
    assert origenes_de_validacion(26) == [14, 17, 20, 23]
    assert pronostico_persistencia([5.0, 7.0]) == [7.0, 7.0, 7.0]
    with pytest.raises(SerieCortaError):
        elegir_mejor_modelo([MetricaValidacion("x", "1 mes(es)", 1.0, 1.0, 4)])
