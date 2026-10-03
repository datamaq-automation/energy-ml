"""src/application/cargas/dtos/identificar_cargas.py — Contratos de entrada/salida de IdentificarCargas."""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class IdentificarCargasRequest(BaseModel):
    medidor: str = Field(min_length=1, examples=["Trafo arriba"])
    desde: datetime
    hasta: datetime

    @model_validator(mode="after")
    def validar_rango(self) -> "IdentificarCargasRequest":
        if self.hasta <= self.desde:
            raise ValueError("'hasta' debe ser posterior a 'desde'.")
        return self


class CargaResponse(BaseModel):
    potencia_tipica_kw: float
    encendidos: int
    apagados: int
    ciclos: int


class IdentificarCargasResponse(BaseModel):
    medidor: str
    mediciones: int
    eventos: int
    potencia_media_kw: float
    cargas: list[CargaResponse]
