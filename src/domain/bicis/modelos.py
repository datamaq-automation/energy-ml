"""src/domain/bicis/modelos.py — Tipos inmutables para la serie diaria de viajes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class DiaViajes:
    """Total de viajes observado en una fecha local."""

    fecha: date
    viajes: int

    def __post_init__(self) -> None:
        if self.viajes < 0:
            raise ValueError("La cantidad de viajes no puede ser negativa.")


@dataclass(frozen=True)
class SerieDiariaViajes:
    """Totales diarios ordenados; los días ausentes no se interpretan como cero."""

    dias: tuple[DiaViajes, ...]

    def __post_init__(self) -> None:
        if not self.dias:
            raise ValueError("La serie diaria debe contener al menos un día.")

        for anterior, actual in zip(self.dias, self.dias[1:], strict=False):
            if actual.fecha == anterior.fecha:
                raise ValueError(f"La serie contiene la fecha duplicada {actual.fecha}.")
            if actual.fecha < anterior.fecha:
                raise ValueError("Las fechas de la serie deben estar en orden ascendente.")

    def dias_faltantes(self, desde: date, hasta: date) -> tuple[date, ...]:
        """Lista fechas ausentes dentro del intervalo inclusivo indicado."""
        if desde > hasta:
            raise ValueError("La fecha inicial no puede ser posterior a la fecha final.")

        presentes = {dia.fecha for dia in self.dias}
        faltantes: list[date] = []
        fecha = desde
        while fecha <= hasta:
            if fecha not in presentes:
                faltantes.append(fecha)
            fecha += timedelta(days=1)
        return tuple(faltantes)


@dataclass(frozen=True)
class VariablesPronostico:
    """Variables conocidas antes del día que se quiere pronosticar."""

    dia_semana: int
    mes: int
    viajes_dia_anterior: int
    viajes_semana_anterior: int
