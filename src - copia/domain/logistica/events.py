"""src/domain/logistica/events.py — Eventos de dominio emitidos al cerrar cada tarea."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Tarea(str, Enum):
    """Las tres tareas del issue #1, en el orden en que se ejecutan."""

    A = "A — K-means y perfiles de negocio"
    B = "B — Clasificación supervisada de retrasos"
    C = "C — Recall por segmento (análisis de errores)"


@dataclass(frozen=True)
class TareaCompletada:
    """Una tarea terminó; `resumen` dice en una línea qué se obtuvo."""

    tarea: Tarea
    resumen: str
