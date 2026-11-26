"""src/application/sibo/dtos/listar_alimentos.py — Entrada y salida del listado de alimentos."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ListarAlimentosRequest(BaseModel):
    """Filtro opcional por nombre o categoría de la base nutricional."""

    model_config = ConfigDict(frozen=True)

    busqueda: str | None = Field(default=None, max_length=80, description="Texto a buscar.")


class AlimentoDTO(BaseModel):
    """Alimento de la base semilla, listo para presentar."""

    model_config = ConfigDict(frozen=True)

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


class ListarAlimentosResponse(BaseModel):
    """Alimentos que pasaron el filtro."""

    model_config = ConfigDict(frozen=True)

    alimentos: list[AlimentoDTO]
