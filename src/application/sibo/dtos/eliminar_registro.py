"""src/application/sibo/dtos/eliminar_registro.py — Entrada y salida de la baja de un registro."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EliminarRegistroRequest(BaseModel):
    """Identificador del registro que se quiere quitar del historial."""

    model_config = ConfigDict(frozen=True)

    registro_id: int = Field(gt=0)


class EliminarRegistroResponse(BaseModel):
    """Confirma qué registro se eliminó."""

    model_config = ConfigDict(frozen=True)

    registro_id: int
