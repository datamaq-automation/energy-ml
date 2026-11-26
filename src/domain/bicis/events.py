"""src/domain/bicis/events.py — Eventos producidos por la evaluación temporal."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PronosticosEvaluados:
    """La corrida terminó y dejó métricas para su período de prueba."""

    informe_id: str
    desde: date
    hasta: date
    dias_prueba: int
