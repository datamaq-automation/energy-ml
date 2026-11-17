"""src/application/sibo/dtos.py — Comandos y modelos de lectura del módulo SIBO."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.sibo.entities import Alimento, PuntoGases, RegistroComida


@dataclass(frozen=True)
class RegistrarComidaCommand:
    """Datos necesarios para registrar una comida consumida."""

    alimento_id: int
    porcion_g: float
    fecha_hora: datetime | None = None
    sintomas: float = 0.0
    notas: str = ""


@dataclass(frozen=True)
class RegistroDetallado:
    """Registro de comida junto con el alimento que lo originó."""

    registro: RegistroComida
    alimento: Alimento


@dataclass(frozen=True)
class SerieGases:
    """Serie temporal de niveles estimados de gases para un rango."""

    rango: str
    desde: datetime
    hasta: datetime
    promedio: float
    pico: float
    puntos: list[PuntoGases]
