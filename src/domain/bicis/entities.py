"""src/domain/bicis/entities.py — Informe identificado de una evaluación temporal."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.domain.bicis.events import PronosticosEvaluados
from src.domain.bicis.value_objects import ResultadoEvaluacionPronosticos


@dataclass(frozen=True)
class InformePronosticos:
    """Resultado de una corrida, identificada y lista para presentar."""

    id: str
    evaluacion: ResultadoEvaluacionPronosticos
    dias_faltantes: tuple[date, ...]
    dias_sin_rezagos: tuple[date, ...]
    eventos: tuple[PronosticosEvaluados, ...]

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("El informe de pronósticos debe tener un identificador.")
