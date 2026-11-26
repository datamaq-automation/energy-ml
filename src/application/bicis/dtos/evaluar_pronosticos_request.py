"""src/application/bicis/dtos/evaluar_pronosticos_request.py — Entrada para evaluar pronósticos."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class EvaluarPronosticosRequest(BaseModel):
    """Identidad de corrida y período que se va a evaluar."""

    model_config = ConfigDict(frozen=True)

    id_informe: str = Field(min_length=1)
    desde: date
    hasta: date
