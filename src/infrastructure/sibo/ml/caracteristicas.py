"""src/infrastructure/sibo/ml/caracteristicas.py — Features de comida, sin etiquetas futuras."""

from __future__ import annotations

from src.domain.sibo.entities import Alimento
from src.domain.sibo.services import factor_fodmap, factor_porcion


def caracteristicas(
    alimento: Alimento,
    porcion_g: float,
    hora: float,
    sintomas: float,
) -> list[float]:
    """Vector usado por el modelo; solo contiene datos conocidos al comer."""
    porcion = factor_porcion(alimento, porcion_g)
    fibra_total = alimento.fibra_g * porcion_g / 100
    carbohidratos_totales = alimento.carbohidratos_g * porcion_g / 100
    hora_normalizada = (hora - 12) / 12
    return [
        factor_fodmap(alimento.fodmap),
        min(alimento.score_inflamatorio / 10, 1.0),
        min(alimento.score_desinflamatorio / 10, 1.0),
        porcion,
        min(fibra_total / 6.0, 1.0),
        min(carbohidratos_totales / 30.0, 1.0),
        min(max(sintomas, 0.0) / 10.0, 1.0),
        hora_normalizada**2,
        min(alimento.kcal / 500.0, 1.0),
        min(alimento.proteinas_g / 30.0, 1.0),
        min(alimento.grasas_g / 30.0, 1.0),
    ]
