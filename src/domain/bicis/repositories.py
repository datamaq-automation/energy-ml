"""src/domain/bicis/repositories.py — Puertos para datos diarios y evaluación de pronósticos."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from src.domain.bicis.value_objects import (
    MuestraPronostico,
    ResultadoEvaluacionPronosticos,
    SerieDiariaViajes,
)


class RepositorioSerieDiaria(Protocol):
    """Fuente de totales diarios para un intervalo de fechas."""

    def obtener(self, desde: date, hasta: date) -> SerieDiariaViajes:
        """Retorna los días disponibles sin completar ausencias con ceros."""
        ...


class ModeladorPronosticos(Protocol):
    """Evalúa los métodos de pronóstico sobre muestras cronológicas."""

    def evaluar(self, muestras: Sequence[MuestraPronostico]) -> ResultadoEvaluacionPronosticos:
        """Ajusta con 2024 y compara con la referencia en 2025."""
        ...
