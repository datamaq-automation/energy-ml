"""Entidades del dominio SIBO (sin dependencias de infraestructura)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Alimento:
    """Alimento de la base nutricional con su propensión inflamatoria."""

    id: int
    nombre: str
    categoria: str
    porcion_base_g: float
    kcal: float
    proteinas_g: float
    carbohidratos_g: float
    grasas_g: float
    fibra_g: float
    fodmap: str
    score_inflamatorio: float
    score_desinflamatorio: float
    notas: str = ""


@dataclass(frozen=True)
class RegistroComida:
    """Comida registrada por el usuario en un instante concreto."""

    fecha_hora: datetime
    alimento_id: int
    porcion_g: float
    sintomas: float = 0.0
    notas: str = ""
    id: int | None = None


@dataclass(frozen=True)
class PuntoGases:
    """Nivel estimado de gases en un instante, con banda de incertidumbre."""

    instante: datetime
    nivel_estimado: float
    nivel_bajo: float
    nivel_alto: float


@dataclass(frozen=True)
class Recomendacion:
    """Alimento sugerido con su puntuación y el motivo de la sugerencia."""

    alimento: Alimento
    puntaje: float
    motivo: str
