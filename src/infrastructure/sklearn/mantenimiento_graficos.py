"""src/infrastructure/sklearn/mantenimiento_graficos.py — Gráficos de codo, silueta y matriz de confusión para mantenimiento."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from matplotlib.figure import Figure

from src.infrastructure.sklearn.mantenimiento_agrupamiento import KMetrics


def save_k_charts(metrics: Sequence[KMetrics], path: Path) -> None:
    """Guarda el gráfico del codo (inercia) y de la silueta para cada k."""
    ks = [item.k for item in metrics]
    figure = Figure(figsize=(9, 4))
    elbow, silhouette = figure.subplots(1, 2)
    elbow.plot(ks, [item.inertia for item in metrics], marker="o")
    elbow.set(title="Codo", xlabel="k", ylabel="Inercia")
    silhouette.plot(ks, [item.silhouette for item in metrics], marker="o")
    silhouette.set(title="Silueta", xlabel="k", ylabel="Silueta media")
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150)


def save_confusion_matrix(tn: int, fp: int, fn: int, tp: int, threshold: float, path: Path) -> None:
    """Guarda la matriz de confusión de la clase 'falla' para un umbral dado."""
    figure = Figure(figsize=(5, 4))
    axis = figure.subplots()
    matrix = [[tn, fp], [fn, tp]]
    axis.imshow(matrix, cmap="Blues")
    for row in range(2):
        for col in range(2):
            axis.text(col, row, str(matrix[row][col]), ha="center", va="center")
    axis.set_xticks([0, 1], labels=["Sin falla", "Falla"])
    axis.set_yticks([0, 1], labels=["Sin falla", "Falla"])
    axis.set(
        title=f"Matriz de confusión (umbral {threshold:.2f})",
        xlabel="Predicho",
        ylabel="Real",
    )
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150)
