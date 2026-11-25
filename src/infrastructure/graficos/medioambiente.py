"""src/infrastructure/graficos/medioambiente.py — Gráficos de codo y silueta de la Tarea A."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.infrastructure.settings.logger import logger


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
