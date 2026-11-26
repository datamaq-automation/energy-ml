"""src/infrastructure/sibo/ml/modelo_hibrido.py — Estimación de gases con etiquetas reales.

Combina un RandomForest con la heurística nutricional solo cuando el primero supera a
la segunda en una validación temporal. La banda se deriva de los errores observados en
esa validación; sin datos reales suficientes se usa la heurística sin banda.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from src.domain.sibo.entities import Alimento, PrediccionPico
from src.domain.sibo.services import puntaje_heuristico
from src.domain.sibo.value_objects import PoliticaModelo
from src.infrastructure.sibo.ml.caracteristicas import caracteristicas
from src.infrastructure.sibo.ml.entrenamiento import MuestraReal, ResultadoEntrenamiento, entrenar


class ModeloGasesHibrido:
    """Predictor de pico de gases (0-100) con banda de error observado."""

    def __init__(
        self,
        politica: PoliticaModelo,
        semilla: int = 42,
        muestras: Sequence[MuestraReal] = (),
    ) -> None:
        self._politica = politica
        self._resultado: ResultadoEntrenamiento = entrenar(muestras, politica, semilla)

    def predecir_pico(
        self,
        alimento: Alimento,
        porcion_g: float,
        hora: float,
        sintomas: float,
    ) -> PrediccionPico:
        heuristica = puntaje_heuristico(alimento, porcion_g, hora, sintomas)
        modelo = self._resultado.modelo
        if modelo is None:
            valor = round(heuristica, 1)
            return PrediccionPico(valor, valor, valor)

        vector = caracteristicas(alimento, porcion_g, hora, sintomas)
        prediccion_modelo = min(max(float(modelo.predict([vector])[0]), 0.0), 100.0)
        pico = _limitar(
            self._resultado.peso_modelo * prediccion_modelo
            + self._resultado.peso_heuristica * heuristica
        )
        if not self._resultado.residuos:
            valor = round(pico, 1)
            return PrediccionPico(valor, valor, valor)

        bajo = _limitar(pico + _percentil(self._resultado.residuos, self._politica.percentil_bajo))
        alto = _limitar(pico + _percentil(self._resultado.residuos, self._politica.percentil_alto))
        return PrediccionPico(
            pico=round(pico, 1),
            bajo=round(min(bajo, pico), 1),
            alto=round(max(alto, pico), 1),
        )

    def estado(self) -> dict[str, bool | float | int | None]:
        """Resume los datos reales y la comparación modelo/heurística."""
        return {
            "muestras_reales": self._resultado.cantidad,
            "muestras_validacion": self._resultado.validacion,
            "modelo_activo": self._resultado.modelo is not None,
            "peso_modelo": self._resultado.peso_modelo,
            "mae_modelo": self._resultado.mae_modelo,
            "mae_heuristica": self._resultado.mae_heuristica,
        }


def _limitar(valor: float) -> float:
    return min(max(valor, 0.0), 100.0)


def _percentil(valores: Sequence[float], percentil: float) -> float:
    ordenados = sorted(valores)
    indice = (len(ordenados) - 1) * percentil / 100.0
    inferior = math.floor(indice)
    superior = math.ceil(indice)
    if inferior == superior:
        return ordenados[inferior]
    fraccion = indice - inferior
    return ordenados[inferior] * (1.0 - fraccion) + ordenados[superior] * fraccion
