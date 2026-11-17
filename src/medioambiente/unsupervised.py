"""src/medioambiente/unsupervised.py — Tarea A: K-means sobre meteorología (T, RH, AH)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from src.infrastructure.settings.logger import logger
from src.medioambiente.preprocess import COLUMNA_ETIQUETA, crear_transformador

# La Tarea A agrupa por las variables meteorológicas de la misma hora: aquí NO hay
# predicción (no hay fuga posible), solo descripción de condiciones.
COLUMNAS_AGROUPAMIENTO: list[str] = ["T", "RH", "AH"]
K_MIN = 2
K_MAX = 6
SEMILLA = 42


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
    """k con mayor coeficiente de silueta (el codo se interpreta en el gráfico)."""
    if resultados.empty:
        raise ValueError("No hay resultados de diagnóstico para elegir k.")
    return int(resultados.loc[resultados["silueta"].idxmax(), "k"])


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
    resumen = df.groupby("grupo")[COLUMNAS_AGROUPAMIENTO].agg(["mean", "size"])
    resumen.columns = ["_".join(col) for col in resumen.columns]
    return resumen.round(2)


def proporcion_episodios(df: pd.DataFrame) -> pd.DataFrame:
    """Proporción de episodios por grupo — SOLO para interpretar, nunca para entrenar."""
    _exigir_grupo(df)
    if COLUMNA_ETIQUETA not in df.columns:
        raise ValueError("Falta 'episodio': aplicá construir_etiqueta() después de agrupar.")
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


def graficar_diagnosticos(resultados: pd.DataFrame, destino: Path) -> tuple[Path, Path]:
    """Guarda los gráficos de codo (inercia) y de silueta en `destino`."""
    import matplotlib

    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt

    destino.mkdir(parents=True, exist_ok=True)
    ruta_codo = destino / "codo_kmeans.png"
    ruta_silueta = destino / "silueta_kmeans.png"

    figura, eje = plt.subplots(figsize=(6, 4))
    eje.plot(resultados["k"], resultados["inercia"], marker="o")
    eje.set_xlabel("k (cantidad de grupos)")
    eje.set_ylabel("Inercia")
    eje.set_title("Método del codo")
    eje.set_xticks(resultados["k"])
    figura.tight_layout()
    figura.savefig(ruta_codo, dpi=120)
    plt.close(figura)

    figura, eje = plt.subplots(figsize=(6, 4))
    eje.plot(resultados["k"], resultados["silueta"], marker="o")
    eje.set_xlabel("k (cantidad de grupos)")
    eje.set_ylabel("Coeficiente de silueta")
    eje.set_title("Coeficiente de silueta")
    eje.set_xticks(resultados["k"])
    figura.tight_layout()
    figura.savefig(ruta_silueta, dpi=120)
    plt.close(figura)

    logger.info("Gráficos de diagnóstico guardados en %s", destino)
    return ruta_codo, ruta_silueta


def _preparar_meteo(df: pd.DataFrame) -> pd.DataFrame:
    """Selecciona T/RH/AH, imputa faltantes (mediana) y escala (StandardScaler)."""
    ausentes = [c for c in COLUMNAS_AGROUPAMIENTO if c not in df.columns]
    if ausentes:
        raise ValueError(f"Faltan columnas para agrupar: {ausentes}")
    transformado = crear_transformador().fit_transform(df[COLUMNAS_AGROUPAMIENTO])
    return pd.DataFrame(transformado, columns=COLUMNAS_AGROUPAMIENTO, index=df.index)


def _exigir_grupo(df: pd.DataFrame) -> None:
    if "grupo" not in df.columns:
        raise ValueError("Falta la columna 'grupo': aplicá agrupar_meteo() primero.")
