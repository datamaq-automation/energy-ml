"""src/application/residuos/dtos/pronosticar_residuos_request.py — Entrada del caso de uso."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PronosticarResiduosRequest(BaseModel):
    """Qué corrida identificar y si se persisten los resultados."""

    model_config = ConfigDict(frozen=True)

    id_informe: str = Field(min_length=1, description="Identidad de la corrida del análisis.")
    guardar_resultados: bool = Field(
        default=True, description="Si es False, solo se calcula (útil para pruebas)."
    )
