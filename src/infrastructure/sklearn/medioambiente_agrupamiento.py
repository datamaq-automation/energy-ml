"""src/infrastructure/sklearn/medioambiente_agrupamiento.py — Tarea A: K-means sobre meteorología (T, RH, AH)."""

from __future__ import annotations

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from src.domain.medioambiente.exceptions import ColumnasFaltantesError
from src.domain.medioambiente.services import elegir_mejor_k
from src.domain.medioambiente.value_objects import (
    COLUMNA_ETIQUETA,
    COLUMNAS_AGRUPAMIENTO,
    K_MAX,
    K_MIN,
    SEMILLA,
    DiagnosticoK,
)
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.medioambiente_preparacion import crear_transformador


def calcular_diagnosticos_k(
    df: pd.DataFrame, k_min: int = K_MIN, k_max: int = K_MAX, semilla: int = SEMILLA
) -> pd.DataFrame:
    """Inercia (codo) y silueta para cada k en [k_min, k_max].

    Imputación (mediana) y escalado con StandardScaler sobre TODO el dataset:
    la Tarea A es exploratoria, no hay split ni evaluación que proteger.
    Se escala porque T, RH y AH tienen unidades y rangos distintos (°C, %, g/m³):
    sin escalar, K-means priorizaría la variable con mayor magnitud numérica.
    """
    escalado = _preparar_meteo(df)
    filas = []
    for k in range(k_min, k_max + 1):
        modelo = KMeans(n_clusters=k, random_state=semilla, n_init=10)
        etiquetas = modelo.fit_predict(escalado)
        filas.append(
            {"k": k, "inercia": modelo.inertia_, "silueta": silhouette_score(escalado, etiquetas)}
        )
    resultados = pd.DataFrame(filas)
    logger.info(
        "Diagnóstico K-means k=%d..%d: mejor silueta=%.3f en k=%d",
        k_min,
        k_max,
        resultados["silueta"].max(),
        mejor_k(resultados),
    )
    return resultados


def mejor_k(resultados: pd.DataFrame) -> int:
    """k con mayor coeficiente de silueta (regla de dominio aplicada a la tabla)."""
    diagnosticos = [
        DiagnosticoK(
            k=int(fila["k"]), inercia=float(fila["inercia"]), silueta=float(fila["silueta"])
        )
        for fila in resultados.to_dict("records")
    ]
    return elegir_mejor_k(diagnosticos)


def agrupar_meteo(df: pd.DataFrame, k: int, semilla: int = SEMILLA) -> pd.DataFrame:
    """Agrega la columna `grupo` con K-means (k clusters) sobre T, RH y AH."""
    escalado = _preparar_meteo(df)
    modelo = KMeans(n_clusters=k, random_state=semilla, n_init=10)
    etiquetas = modelo.fit_predict(escalado)
    salida = df.copy()
    salida["grupo"] = etiquetas.astype("int16")
    logger.info("K-means con k=%d: grupos=%s", k, sorted({int(e) for e in etiquetas}))
    return salida


def resumen_grupos(df: pd.DataFrame) -> pd.DataFrame:
    """Media de T, RH y AH por grupo (insumo para describir cada grupo)."""
    _exigir_grupo(df)
    resumen = df.groupby("grupo")[COLUMNAS_AGRUPAMIENTO].agg(["mean", "size"])
    resumen.columns = ["_".join(col) for col in resumen.columns]
    return resumen.round(2)


def proporcion_episodios(df: pd.DataFrame) -> pd.DataFrame:
    """Proporción de episodios por grupo — SOLO para interpretar, nunca para entrenar."""
    _exigir_grupo(df)
    if COLUMNA_ETIQUETA not in df.columns:
        raise ColumnasFaltantesError(
            "Falta 'episodio': aplicá construir_etiqueta() después de agrupar.", [COLUMNA_ETIQUETA]
        )
    etiquetado = df.dropna(subset=[COLUMNA_ETIQUETA])
    resumen = etiquetado.groupby("grupo")[COLUMNA_ETIQUETA].agg(
        n_horas="size", proporcion_episodio="mean"
    )
    resumen["proporcion_episodio"] = resumen["proporcion_episodio"].round(3)
    logger.info(
        "Proporción de episodios por grupo calculada sobre %d/%d filas con etiqueta",
        len(etiquetado),
        len(df),
    )
    return resumen


def _preparar_meteo(df: pd.DataFrame) -> pd.DataFrame:
    """Selecciona T/RH/AH, imputa faltantes (mediana) y escala (StandardScaler)."""
    ausentes = [c for c in COLUMNAS_AGRUPAMIENTO if c not in df.columns]
    if ausentes:
        raise ColumnasFaltantesError(f"Faltan columnas para agrupar: {ausentes}", ausentes)
    transformado = crear_transformador().fit_transform(df[COLUMNAS_AGRUPAMIENTO])
    return pd.DataFrame(transformado, columns=COLUMNAS_AGRUPAMIENTO, index=df.index)


def _exigir_grupo(df: pd.DataFrame) -> None:
    if "grupo" not in df.columns:
        raise ColumnasFaltantesError(
            "Falta la columna 'grupo': aplicá agrupar_meteo() primero.", ["grupo"]
        )
