"""src/application/cargas/dtos/mediciones_fuente.py — Respuesta de fuente de mediciones."""

from pydantic import BaseModel, Field


class UltimaDescargaResponse(BaseModel):
    """Metadatos de la última descarga (solo en modo SSH)."""

    instante: str | None = Field(
        None, description="Timestamp ISO de la última descarga (null si no ocurrió aún)"
    )
    duracion_segundos: float = Field(default=0.0, description="Duración de la descarga en segundos")
    filas_por_medidor: dict[str, int] = Field(
        default_factory=dict, description="Cantidad de filas por medidor descargado"
    )


class MedicionesFuenteResponse(BaseModel):
    """Información sobre la fuente actual de mediciones."""

    fuente: str = Field(description="'local' (data/input/) o 'ssh' (VPS via Tailscale)")
    medidores: list[str] = Field(description="Medidores disponibles en la fuente actual")
    ultima_descarga: UltimaDescargaResponse | None = Field(
        None, description="Metadatos de descarga (null en modo local)"
    )
