"""src/application/residuos/dtos/pronosticar_residuos_response.py — Salida del caso de uso."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MetricaValidacionDTO(BaseModel):
    """MAE y RMSE de un modelo para un horizonte (o el bloque completo)."""

    model_config = ConfigDict(frozen=True)

    modelo: str
    horizonte: str
    mae_toneladas: float
    rmse_toneladas: float
    predicciones_evaluadas: int


class PronosticoDTO(BaseModel):
    """Toneladas pronosticadas por un modelo para un mes."""

    model_config = ConfigDict(frozen=True)

    mes: str
    modelo: str
    toneladas: float


class PronosticarResiduosResponse(BaseModel):
    """Serie, validación y pronóstico listos para presentar."""

    model_config = ConfigDict(frozen=True)

    id_informe: str
    meses: int
    primer_mes: str
    ultimo_mes: str
    metricas: list[MetricaValidacionDTO]
    pronosticos: list[PronosticoDTO]
    mejor_modelo: str
    archivos: list[str]
    eventos: list[str]
