"""src/domain/residuos/services.py — Reglas puras de la validación temporal y la línea base."""

from __future__ import annotations

from collections.abc import Iterable

from src.domain.residuos.exceptions import SerieCortaError
from src.domain.residuos.value_objects import (
    FORECAST_HORIZON,
    HORIZONTE_COMPLETO,
    LAG_MONTHS,
    VALIDATION_MONTHS,
    MetricaValidacion,
)


def origenes_de_validacion(meses: int) -> list[int]:
    """Índices donde arranca cada bloque de 3 meses del último año (sin solapamiento)."""
    primer_origen = meses - VALIDATION_MONTHS
    if primer_origen <= LAG_MONTHS:
        raise SerieCortaError("La serie es demasiado corta para la validación temporal solicitada.")
    origenes = list(range(primer_origen, meses, FORECAST_HORIZON))
    if meses - origenes[-1] < FORECAST_HORIZON:
        raise SerieCortaError("El período de validación no contiene bloques completos de 3 meses.")
    return origenes


def pronostico_persistencia(
    historia: list[float], horizonte: int = FORECAST_HORIZON
) -> list[float]:
    """Línea base: cada mes futuro repite el último mes observado."""
    return [historia[-1]] * horizonte


def elegir_mejor_modelo(metricas: Iterable[MetricaValidacion]) -> MetricaValidacion:
    """Menor MAE sobre el bloque completo de 3 meses (ante empate, el primero listado)."""
    completas = [m for m in metricas if m.horizonte == HORIZONTE_COMPLETO]
    if not completas:
        raise SerieCortaError("No hay métricas del horizonte completo para comparar modelos.")
    return min(completas, key=lambda metrica: metrica.mae_toneladas)
