"""Servicios puros del dominio SIBO: heurísticas explicables y curva de absorción."""

from __future__ import annotations

import math

from sibo.domain.entities import Alimento

FODMAP_VALOR = {"bajo": 0.1, "medio": 0.5, "alto": 0.9}
VENTANA_DIGESTION_HORAS = 8.0
HORA_PICO_HORAS = 2.0


def factor_fodmap(fodmap: str) -> float:
    """Normaliza la categoría FODMAP a un valor entre 0 y 1."""
    return FODMAP_VALOR.get(fodmap.lower(), 0.5)


def factor_porcion(alimento: Alimento, porcion_g: float) -> float:
    """Cuántas porciones base representa lo consumido (acotado para evitar outliers)."""
    if alimento.porcion_base_g <= 0:
        return 1.0
    return min(max(porcion_g / alimento.porcion_base_g, 0.1), 3.0)


def puntaje_heuristico(
    alimento: Alimento,
    porcion_g: float,
    hora: float,
    sintomas: float,
) -> float:
    """Nivel de gases esperado (0-100) según reglas nutricionales transparentes.

    Es la parte explicable del modelo híbrido: sube con FODMAP, fibra, carbohidratos,
    score inflamatorio, tamaño de porción y síntomas; baja con el score desinflamatorio.
    """
    porcion = factor_porcion(alimento, porcion_g)
    fibra_total = alimento.fibra_g * porcion_g / 100
    carbohidratos_totales = alimento.carbohidratos_g * porcion_g / 100
    hora_normalizada = (hora - 12) / 12

    puntaje = (
        8.0
        + 34.0 * factor_fodmap(alimento.fodmap)
        + 16.0 * min(fibra_total / 6.0, 1.0)
        + 14.0 * min(carbohidratos_totales / 30.0, 1.0)
        + 22.0 * alimento.score_inflamatorio / 10.0
        - 12.0 * alimento.score_desinflamatorio / 10.0
        + 10.0 * min((porcion - 1.0) / 2.0, 1.0)
        + 8.0 * min(max(sintomas, 0.0) / 10.0, 1.0)
        + 6.0 * hora_normalizada**2
    )
    return min(max(puntaje, 0.0), 100.0)


def curva_absorcion(horas: float) -> float:
    """Forma de la curva de gases desde que se come: 0 antes, pico a las 2 h, 0 a las 8 h."""
    if horas < 0 or horas > VENTANA_DIGESTION_HORAS:
        return 0.0
    x = horas / HORA_PICO_HORAS
    return x * math.exp(1.0 - x)


def motivo_recomendacion(alimento: Alimento, consumido_recientemente: bool) -> str:
    """Explica en lenguaje natural por qué se sugiere un alimento."""
    razones: list[str] = []
    if alimento.fodmap == "bajo":
        razones.append("bajo en FODMAP")
    if alimento.score_desinflamatorio >= 7:
        razones.append("alto efecto desinflamatorio")
    elif alimento.score_desinflamatorio >= 5:
        razones.append("aporta propiedades desinflamatorias")
    if alimento.fibra_g >= 2:
        razones.append("aporta fibra")
    if alimento.score_inflamatorio <= 3:
        razones.append("bajo potencial irritante")
    if not razones:
        razones.append("opción suave para variar la dieta")
    motivo = "Recomendado por ser " + ", ".join(razones)
    if consumido_recientemente:
        motivo += ". Ya lo registraste esta semana: alterná con otras opciones"
    return motivo
