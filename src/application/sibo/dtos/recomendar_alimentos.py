"""src/application/sibo/dtos/recomendar_alimentos.py — Entrada y salida de recomendaciones."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.application.sibo.dtos.listar_alimentos import AlimentoDTO


class RecomendarAlimentosRequest(BaseModel):
    """Cantidad máxima de sugerencias a devolver."""

    model_config = ConfigDict(frozen=True)

    limite: int = Field(default=6, ge=1, le=20)


class RecomendacionDTO(BaseModel):
    """Alimento sugerido con puntaje y explicación en lenguaje natural."""

    model_config = ConfigDict(frozen=True)

    alimento: AlimentoDTO
    puntaje: float
    motivo: str


class RecomendarAlimentosResponse(BaseModel):
    """Lista ordenada de sugerencias para el período reciente."""

    model_config = ConfigDict(frozen=True)

    recomendaciones: list[RecomendacionDTO]
