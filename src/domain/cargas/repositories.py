"""src/domain/cargas/repositories.py — Puertos (interfaces) que el dominio necesita del exterior."""

from datetime import datetime
from typing import Protocol

from src.domain.cargas.entities import Carga, EventoCarga, EventoReal, Medicion


class MedicionRepository(Protocol):
    """Fuente de series de potencia por medidor."""

    def listar(self, medidor: str, desde: datetime, hasta: datetime) -> list[Medicion]: ...


class Bitacora(Protocol):
    """Registro de lo que hace el proceso (solo info, warning y error)."""

    def info(self, msg: str, *args: object) -> None: ...

    def warning(self, msg: str, *args: object) -> None: ...

    def error(self, msg: str, *args: object) -> None: ...


class AgrupadorEventos(Protocol):
    """Agrupa eventos por magnitud; devuelve una etiqueta por evento (-1 = ruido)."""

    def agrupar(self, eventos: list[EventoCarga], radio_kw: float, min_eventos: int) -> list[int]: ...


class CargaRepository(Protocol):
    """Destino de las cargas identificadas de cada medidor."""

    def guardar(self, medidor: str, cargas: list[Carga]) -> None: ...


class VerdadRepository(Protocol):
    """Eventos reales de un medidor simulado: lo que el algoritmo debería encontrar."""

    def guardar(self, medidor: str, eventos: list[EventoReal]) -> None: ...

    def listar(self, medidor: str) -> list[EventoReal]: ...
