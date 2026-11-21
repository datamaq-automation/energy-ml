"""src/infrastructure/graficos/educacion.py — Gráficos de codo y silueta de la Tarea A."""

from __future__ import annotations


def plot_elbow_silhouette(
    k_values: list[int],
    inertias: list[float],
    silhouettes: list[float],
) -> None:
    """Muestra los gráficos de codo y silueta en pantalla (sin guardar archivos)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(k_values, inertias, marker="o")
    axes[0].set_title("Codo (inercia)")
    axes[0].set_xlabel("k")
    axes[0].set_ylabel("Inercia")
    axes[1].plot(k_values, silhouettes, marker="o")
    axes[1].set_title("Silueta")
    axes[1].set_xlabel("k")
    axes[1].set_ylabel("Score de silueta")
    fig.tight_layout()
    plt.show()
    plt.close(fig)


class MatplotlibGraficador:
    """Implementa GraficadorGrupos: codo y silueta en pantalla, nunca en disco."""

    def mostrar_codo_silueta(
        self, k_values: list[int], inertias: list[float], silhouettes: list[float]
    ) -> None:
        """Delega en plot_elbow_silueta (solo pantalla, sin archivos)."""
        plot_elbow_silhouette(k_values, inertias, silhouettes)
