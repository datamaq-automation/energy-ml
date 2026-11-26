"""src/domain/sibo/events.py — Hechos del dominio al registrar o borrar comidas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ComidaRegistrada:
    """Una comida quedó registrada con su alimento, porción y contexto."""

    registro_id: int
    alimento_id: int
    fecha_hora: datetime
    porcion_g: float


@dataclass(frozen=True)
class RegistroEliminado:
    """Un registro de comida salió del historial del usuario."""

    registro_id: int
