"""src/domain/residuos/events.py — Eventos de dominio emitidos al cerrar cada etapa."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Etapa(str, Enum):
    """Etapas del caso del issue #8, en el orden en que se ejecutan."""

    SERIE = "Serie mensual de la ciudad"
    VALIDACION = "Validación temporal (último año, bloques de 3 meses)"
    PRONOSTICO = "Pronóstico de los 3 meses siguientes"


@dataclass(frozen=True)
class EtapaCompletada:
    """Una etapa terminó; `resumen` dice en una línea qué se obtuvo."""

    etapa: Etapa
    resumen: str
