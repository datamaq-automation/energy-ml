"""tests/unit/bicis/test_evaluar_pronosticos_use_case.py — Orquestación de evaluación."""

from collections.abc import Sequence
from datetime import date, timedelta

from src.application.bicis.dtos.evaluar_pronosticos_request import EvaluarPronosticosRequest
from src.application.bicis.use_cases.evaluar_pronosticos import EvaluarPronosticosUseCase
from src.application.bicis.use_cases.preparar_pronosticos import PrepararPronosticosUseCase
from src.domain.bicis.value_objects import (
    DiaViajes,
    MetricasPronostico,
    MuestraPronostico,
    ResultadoEvaluacionPronosticos,
    SerieDiariaViajes,
)


class RepositorioEnMemoria:
    def __init__(self) -> None:
        inicio = date(2024, 1, 1)
        hasta = date(2025, 1, 4)
        dias: list[DiaViajes] = []
        fecha = inicio
        while fecha <= hasta:
            dias.append(DiaViajes(fecha, len(dias) + 1))
            fecha += timedelta(days=1)
        self.serie = SerieDiariaViajes(tuple(dias))

    def obtener(self, desde: date, hasta: date) -> SerieDiariaViajes:
        return self.serie


class ModeladorFalso:
    def evaluar(self, muestras: Sequence[MuestraPronostico]) -> ResultadoEvaluacionPronosticos:
        entrenamiento = sum(m.fecha_objetivo.year == 2024 for m in muestras)
        prueba = sum(m.fecha_objetivo.year == 2025 for m in muestras)
        return ResultadoEvaluacionPronosticos(
            linea_base=MetricasPronostico("Referencia", 2.0, 3.0),
            bosque_aleatorio=MetricasPronostico("Modelo", 1.0, 2.0),
            dias_entrenamiento=entrenamiento,
            dias_prueba=prueba,
        )


def test_evaluar_pronosticos_devuelve_metricas_cobertura_y_evento() -> None:
    preparador = PrepararPronosticosUseCase(RepositorioEnMemoria())
    caso_de_uso = EvaluarPronosticosUseCase(preparador, ModeladorFalso())

    respuesta = caso_de_uso.execute(
        EvaluarPronosticosRequest(
            id_informe="prueba-1",
            desde=date(2024, 1, 1),
            hasta=date(2025, 1, 4),
        )
    )

    assert respuesta.id_informe == "prueba-1"
    assert respuesta.dias_entrenamiento == 359
    assert respuesta.dias_prueba == 4
    assert respuesta.linea_base.mae == 2.0
    assert respuesta.bosque_aleatorio.mae == 1.0
    assert respuesta.dias_sin_rezagos == tuple(date(2024, 1, day) for day in range(1, 8))
    assert respuesta.eventos == (
        "Pronósticos evaluados del 2024-01-01 al 2025-01-04: 4 días de prueba",
    )
