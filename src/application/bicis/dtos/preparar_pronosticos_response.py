"""src/application/bicis/dtos/preparar_pronosticos_response.py — Muestras y exclusiones preparadas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict

from src.domain.bicis.value_objects import MuestraPronostico


class PrepararPronosticosResponse(BaseModel):
    """Muestras utilizables y fechas excluidas por faltantes o falta de rezagos."""

    model_config = ConfigDict(frozen=True)

    muestras: tuple[MuestraPronostico, ...]
    dias_faltantes: tuple[date, ...]
    dias_sin_rezagos: tuple[date, ...]
