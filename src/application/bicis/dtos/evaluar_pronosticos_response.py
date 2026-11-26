"""src/application/bicis/dtos/evaluar_pronosticos_response.py — Informe de métricas y cobertura."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict

from src.domain.bicis.value_objects import MetricasPronostico


class EvaluarPronosticosResponse(BaseModel):
    """Resultados de la comparación temporal listos para presentar."""

    model_config = ConfigDict(frozen=True)

    id_informe: str
    linea_base: MetricasPronostico
    bosque_aleatorio: MetricasPronostico
    dias_entrenamiento: int
    dias_prueba: int
    dias_faltantes: tuple[date, ...]
    dias_sin_rezagos: tuple[date, ...]
    eventos: tuple[str, ...]
