"""src/adapters/sibo/controllers/esquemas.py — Esquemas de entrada HTTP del módulo SIBO."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RegistroCreateRequest(BaseModel):
    alimento_id: int = Field(gt=0)
    porcion_g: float = Field(gt=0, le=5000)
    fecha_hora: datetime | None = None
    sintomas: float = Field(default=0.0, ge=0, le=10)
    notas: str = Field(default="", max_length=500)
