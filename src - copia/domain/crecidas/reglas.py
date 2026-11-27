"""src/domain/crecidas/reglas.py — Reglas puras de escenario y alerta temprana."""

from __future__ import annotations

from src.domain.crecidas.modelos import AlertaTemprana, Escenario, Umbrales


def clasificar_escenario(nivel_m: float, umbrales: Umbrales) -> Escenario:
    """Clasifica un nivel de río según los umbrales.

    Los límites inferiores son inclusivos: nivel == alerta_m ya es ALERTA.
    """
    if nivel_m >= umbrales.crecida_m:
        return Escenario.CRECIDA
    if nivel_m >= umbrales.alerta_m:
        return Escenario.ALERTA
    if nivel_m >= umbrales.vigilancia_m:
        return Escenario.VIGILANCIA
    return Escenario.NORMAL


def generar_alerta(
    nivel_previsto_m: float,
    horizonte_horas: int,
    umbrales: Umbrales,
) -> AlertaTemprana | None:
    """Devuelve una AlertaTemprana si el nivel previsto es de alerta o crecida; si no, None."""
    if horizonte_horas <= 0:
        raise ValueError("El horizonte debe ser mayor que cero")

    escenario = clasificar_escenario(nivel_previsto_m, umbrales)
    if escenario == Escenario.ALERTA:
        umbral = umbrales.alerta_m
    elif escenario == Escenario.CRECIDA:
        umbral = umbrales.crecida_m
    else:
        return None

    return AlertaTemprana(
        escenario=escenario,
        nivel_previsto_m=nivel_previsto_m,
        horizonte_horas=horizonte_horas,
        umbral_disparado_m=umbral,
    )
