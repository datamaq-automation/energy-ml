"""src/application/sibo/dtos/consultar_registros.py — Entrada y salida del historial de comidas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.application.sibo.dtos.registrar_comida import RegistrarComidaResponse


class ConsultarRegistrosRequest(BaseModel):
    """Ventana temporal opcional para consultar el historial."""

    model_config = ConfigDict(frozen=True)

    desde: datetime | None = None
    hasta: datetime | None = None


class ConsultarRegistrosResponse(BaseModel):
    """Registros del período, ya enriquecidos con sus alimentos."""

    model_config = ConfigDict(frozen=True)

    registros: list[RegistrarComidaResponse]
