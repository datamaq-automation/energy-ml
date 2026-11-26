"""src/application/sibo/dtos/registrar_comida.py — Entrada y salida del registro de comidas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RegistrarComidaRequest(BaseModel):
    """Datos de la comida que se va a persistir."""

    model_config = ConfigDict(frozen=True)

    alimento_id: int = Field(gt=0)
    porcion_g: float = Field(gt=0, le=5000)
    fecha_hora: datetime | None = None
    sintomas: float = Field(default=0.0, ge=0, le=10)
    notas: str = Field(default="", max_length=500)


class RegistrarComidaResponse(BaseModel):
    """Comida guardada junto con la información del alimento que la originó."""

    model_config = ConfigDict(frozen=True)

    id: int
    fecha_hora: datetime
    alimento_id: int
    alimento_nombre: str
    categoria: str
    fodmap: str
    porcion_g: float
    sintomas: float
    notas: str
    sintomas_2h: float | None = None
    fecha_sintomas_2h: datetime | None = None
    score_inflamatorio: float
    score_desinflamatorio: float
