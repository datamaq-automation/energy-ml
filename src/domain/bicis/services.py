"""src/domain/bicis/services.py — Reglas puras para preparar variables y validar períodos."""

from __future__ import annotations

from datetime import date, timedelta

from src.domain.bicis.exceptions import PeriodoPronosticoInvalidoError
from src.domain.bicis.value_objects import SerieDiariaViajes, VariablesPronostico


def validar_periodo(desde: date, hasta: date) -> None:
    """Rechaza rangos invertidos antes de consultar cualquier fuente de datos."""
    if desde > hasta:
        raise PeriodoPronosticoInvalidoError(
            "La fecha inicial no puede ser posterior a la fecha final."
        )


def viajes_mismo_dia_semana_anterior(serie: SerieDiariaViajes, fecha_objetivo: date) -> int | None:
    """Devuelve viajes[t-7], o None si ese dato anterior no está disponible."""
    fecha_referencia = fecha_objetivo - timedelta(days=7)
    for dia in serie.dias:
        if dia.fecha == fecha_referencia:
            return dia.viajes
    return None


def construir_variables_pronostico(
    serie: SerieDiariaViajes, fecha_objetivo: date
) -> VariablesPronostico | None:
    """Construye calendario y rezagos previos; no consulta el día objetivo ni el futuro."""
    viajes_por_fecha = {dia.fecha: dia.viajes for dia in serie.dias if dia.fecha < fecha_objetivo}
    viajes_dia_anterior = viajes_por_fecha.get(fecha_objetivo - timedelta(days=1))
    viajes_semana_anterior = viajes_por_fecha.get(fecha_objetivo - timedelta(days=7))
    if viajes_dia_anterior is None or viajes_semana_anterior is None:
        return None

    return VariablesPronostico(
        dia_semana=fecha_objetivo.weekday(),
        mes=fecha_objetivo.month,
        viajes_dia_anterior=viajes_dia_anterior,
        viajes_semana_anterior=viajes_semana_anterior,
    )
