"""src/domain/medioambiente/services.py — Reglas puras del caso de episodios de CO."""

from __future__ import annotations

from collections.abc import Iterable

from src.domain.medioambiente.exceptions import FugaDeDatosError, SinDiagnosticosError
from src.domain.medioambiente.value_objects import (
    COLUMNAS_PROHIBIDAS,
    UMBRAL_CAMBIO,
    DiagnosticoK,
    MetricasModelo,
)


def elegir_mejor_k(diagnosticos: Iterable[DiagnosticoK]) -> int:
    """k con mayor coeficiente de silueta (el codo se interpreta en el gráfico)."""
    lista = list(diagnosticos)
    if not lista:
        raise SinDiagnosticosError("No hay resultados de diagnóstico para elegir k.")
    return max(lista, key=lambda diagnostico: diagnostico.silueta).k


def elegir_mejor_modelo(metricas: Iterable[MetricasModelo]) -> MetricasModelo:
    """Modelo con mayor F1 de la clase 'episodio' (ante empate, el primero listado)."""
    lista = list(metricas)
    if not lista:
        raise ValueError("No hay métricas para elegir un modelo.")
    return max(lista, key=lambda metrica: metrica.f1)


def verificar_sin_fuga(features: Iterable[str]) -> None:
    """Rechaza features que salen de la misma hora a predecir o que generan la etiqueta."""
    filtradas = [columna for columna in features if columna in COLUMNAS_PROHIBIDAS]
    if filtradas:
        raise FugaDeDatosError(filtradas)


def desvio_estandarizado(media_train: float, media_test: float, desvio_train: float) -> float:
    """Desplazamiento de la media de test medido en desvíos estándar de train."""
    if desvio_train > 0:
        return (media_test - media_train) / desvio_train
    return 0.0


def hay_cambio(desvio: float, umbral: float = UMBRAL_CAMBIO) -> bool:
    """Cambio de distribución tipo invierno → verano: |desvío| supera el umbral."""
    return bool(abs(desvio) > umbral)
