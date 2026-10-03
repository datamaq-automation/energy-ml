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
    ciclos_por_dia: float | None = Field(default=None, description="None si el rango es menor a un día")
    on_off: bool = Field(default=True, description="Encendidos y apagados parecidos: se comporta como un equipo ON/OFF")


class BarraHistogramaResponse(BaseModel):
    desde_kw: float
    hasta_kw: float
    cantidad: int


class UmbralResponse(BaseModel):
    kw: float | None = Field(description="Umbral |ΔP| usado; None si no se pudo estimar")
    automatico: bool
    separacion: float | None = Field(default=None, description="η de Otsu (solo si es automático)")
    confiable: bool | None = Field(default=None, description="η >= separación mínima (solo si es automático)")


class IdentificarCargasResponse(BaseModel):
    medidor: str
    mediciones: int
    eventos: int
    encendidos: int = 0
    apagados: int = 0
    eventos_sin_grupo: int = Field(default=0, description="Eventos que DBSCAN dejó como ruido")
    dias: float = Field(default=0.0, description="Días cubiertos por las mediciones")
    potencia_media_kw: float
    cargas: list[CargaResponse]
    umbral: UmbralResponse
    histograma: list[BarraHistogramaResponse] = Field(description="Distribución de |ΔP|: ruido a la izquierda, eventos a la derecha")
