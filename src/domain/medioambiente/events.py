"""src/domain/medioambiente/events.py — Eventos de dominio emitidos al cerrar cada tarea."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Tarea(str, Enum):
    """Las tres tareas del issue #7, en el orden en que se ejecutan."""

    A = "A — K-means sobre meteorología (sin etiqueta)"
    B = "B — Modelos con split aleatorio estratificado"
    C = "C — Split temporal (80 % más antiguo → 20 % más reciente)"


@dataclass(frozen=True)
class TareaCompletada:
    """Una tarea terminó; `resumen` dice en una línea qué se obtuvo."""

    tarea: Tarea
    resumen: str
