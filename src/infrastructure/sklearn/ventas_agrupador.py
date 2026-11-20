"""src/infrastructure/sklearn/ventas_agrupador.py — Tarea A: fichas por serie, escalado y K-means."""

from __future__ import annotations

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from src.domain.ventas.modelos import Agrupamiento, MetricaGrupos, PerfilGrupo

DIAS: dict[int, str] = {0: "lun", 1: "mar", 2: "mie", 3: "jue", 4: "vie", 5: "sab", 6: "dom"}


def armar_fichas(ventas: pd.DataFrame) -> pd.DataFrame:
    """Una ficha por (tienda, producto): promedio, desvío y promedio de cada día de la semana.

    La proporción de días sin venta se descartó: en todo el dataset hay un solo día con venta cero.
    """
    fichas = ventas.groupby(["store", "item"])["sales"].agg(["mean", "std"])
    dia = ventas["date"].dt.day_of_week
    semana = ventas.groupby(["store", "item", dia])["sales"].mean().unstack()
    return fichas.join(semana.rename(columns=DIAS))


class KMeansAgrupadorVentas:
    """Implementa AgrupadorSeries con StandardScaler + KMeans (random_state=42)."""

    def agrupar(
        self, ventas: pd.DataFrame, valores_k: tuple[int, ...], k_elegido: int
    ) -> Agrupamiento:
        """Evalúa codo y silueta para cada k y asigna grupos con el k elegido."""
        fichas = armar_fichas(ventas)
        escaladas = StandardScaler().fit_transform(fichas)

        metricas = []
        for k in valores_k:
            modelo = KMeans(n_clusters=k, random_state=42, n_init=10).fit(escaladas)
            silueta = float(silhouette_score(escaladas, modelo.labels_))
            metricas.append(MetricaGrupos(k=k, inercia=float(modelo.inertia_), silueta=silueta))

        modelo = KMeans(n_clusters=k_elegido, random_state=42, n_init=10).fit(escaladas)
        fichas["grupo"] = modelo.labels_
        resumen = fichas.groupby("grupo")["mean"].agg(["size", "mean"])
        perfiles = tuple(
            PerfilGrupo(
                grupo=int(g), cantidad_series=int(fila["size"]), venta_media=float(fila["mean"])
            )
            for g, fila in resumen.iterrows()
        )
        grupo_por_serie = {(int(s), int(i)): int(g) for (s, i), g in fichas["grupo"].items()}
        return Agrupamiento(tuple(metricas), perfiles, grupo_por_serie)
