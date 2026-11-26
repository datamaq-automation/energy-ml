"""src/application/sibo/dtos/registrar_sintomas_2h.py — Entrada y salida del seguimiento a las 2 h."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RegistrarSintomas2HRequest(BaseModel):
    """Etiqueta real observada después de una comida."""

    model_config = ConfigDict(frozen=True)

    registro_id: int = Field(gt=0)
    sintomas: float = Field(ge=0, le=10)
    fecha: datetime | None = None


class RegistrarSintomas2HResponse(BaseModel):
    """Confirma la etiqueta guardada y cuándo se midió."""

    model_config = ConfigDict(frozen=True)

    registro_id: int
    sintomas: float
    fecha: datetime
