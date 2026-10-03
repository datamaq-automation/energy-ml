"""src/domain/cargas/repositories.py — Puertos (interfaces) que el dominio necesita del exterior."""

from datetime import datetime
from typing import Protocol

from src.domain.cargas.entities import EventoCarga, Medicion


class MedicionRepository(Protocol):
    """Fuente de series de potencia por medidor."""

    def listar(self, medidor: str, desde: datetime, hasta: datetime) -> list[Medicion]: ...


class AgrupadorEventos(Protocol):
    """Agrupa eventos por magnitud; devuelve una etiqueta por evento (-1 = ruido)."""

    def agrupar(self, eventos: list[EventoCarga]) -> list[int]: ...
