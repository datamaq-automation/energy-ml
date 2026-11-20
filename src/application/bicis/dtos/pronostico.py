"""src/application/bicis/dtos/pronostico.py — Datos preparados para evaluar pronósticos diarios."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.domain.bicis.modelos import VariablesPronostico


@dataclass(frozen=True)
class MuestraPronostico:
    """Un día con sus entradas disponibles antes del pronóstico y su valor observado."""

    fecha_objetivo: date
    variables: VariablesPronostico
    viajes_reales: int


@dataclass(frozen=True)
class ResultadoPreparacionPronosticos:
    """Muestras utilizables y fechas que se excluyeron por datos o rezagos ausentes."""

    muestras: tuple[MuestraPronostico, ...]
    dias_faltantes: tuple[date, ...]
    dias_sin_rezagos: tuple[date, ...]
