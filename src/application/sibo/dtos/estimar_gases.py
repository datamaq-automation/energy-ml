"""src/application/sibo/dtos/estimar_gases.py — Entrada y salida de la curva de gases."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class EstimarGasesRequest(BaseModel):
    """Rango temporal y día de referencia de la curva solicitada."""

    model_config = ConfigDict(frozen=True)

    rango: str = Field(default="dia", pattern="^(dia|semana|mes)$")
    fecha: date | None = None


class PuntoGasesDTO(BaseModel):
    """Nivel estimado en un instante con la dispersión del ensamble."""

    model_config = ConfigDict(frozen=True)

    instante: datetime
    nivel_estimado: float
    nivel_bajo: float
    nivel_alto: float


class EstimarGasesResponse(BaseModel):
    """Serie temporal con resumen y puntos de la curva."""

    model_config = ConfigDict(frozen=True)

    rango: str
    desde: datetime
    hasta: datetime
    promedio: float
    pico: float
    puntos: list[PuntoGasesDTO]
