"""src/adapters/sibo/presenters/respuestas.py — Modelos HTTP de la API SIBO."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AlimentoResponse(BaseModel):
    """Alimento con su información nutricional."""

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
    notas: str


class RegistroResponse(BaseModel):
    """Comida registrada junto con el alimento que la originó."""

    id: int
    fecha_hora: datetime
    alimento_id: int
    alimento_nombre: str
    categoria: str
    fodmap: str
    porcion_g: float
    sintomas: float
    notas: str
    score_inflamatorio: float
    score_desinflamatorio: float


class PuntoGasesResponse(BaseModel):
    """Nivel estimado de gases en un instante."""

    instante: datetime
    nivel_estimado: float
    nivel_bajo: float
    nivel_alto: float


class SerieGasesResponse(BaseModel):
    """Curva de gases con su escala declarada."""

    rango: str
    desde: datetime
    hasta: datetime
    unidad: str = "nivel relativo 0-100"
    promedio: float
    pico: float
    puntos: list[PuntoGasesResponse]


class RecomendacionResponse(BaseModel):
    """Sugerencia de alimento con su explicación."""

    alimento: AlimentoResponse
    puntaje: float
    motivo: str


class SaludResponse(BaseModel):
    """Estado del módulo."""

    status: str
    modulo: str
    version: str
