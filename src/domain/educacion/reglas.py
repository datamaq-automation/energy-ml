"""src/domain/educacion/reglas.py — Reglas puras del caso educacion (sin dependencias externas)."""

from __future__ import annotations

from typing import Any

from src.domain.educacion.modelos import FAIL_THRESHOLD


def etiqueta_desaprobado(g3: Any) -> Any:
    """Etiqueta vectorizada 'desaprobado = G3 < FAIL_THRESHOLD' (solo G3 decide).

    Trabaja por polimorfismo de tipos: recibe la columna G3 (Serie de pandas) y
    devuelve 1 donde G3 < umbral y 0 en el resto. El dominio no importa pandas.
    """
    return (g3 < FAIL_THRESHOLD).astype(int)


def choose_k(k_values: list[int], silhouettes: list[float]) -> int:
    """Elige k por mayor score de silueta, en complemento a la lectura del codo."""
    if not k_values or len(k_values) != len(silhouettes):
        raise ValueError("k_values y silhouettes deben ser listas no vacías de igual longitud.")
    return k_values[max(range(len(silhouettes)), key=silhouettes.__getitem__)]
