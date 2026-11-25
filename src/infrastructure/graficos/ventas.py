"""src/infrastructure/graficos/ventas.py — Gráficos de ventas: codo y silueta (A) y real vs pronóstico (B)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.domain.ventas.modelos import MetricaGrupos, Pronosticos, Serie  # noqa: E402


def guardar_codo_silueta(metricas: tuple[MetricaGrupos, ...], ruta: Path) -> None:
    """Dos gráficos lado a lado para elegir k: inercia (codo) y silueta."""
    ks = [m.k for m in metricas]
    fig, (izq, der) = plt.subplots(1, 2, figsize=(10, 4))
    izq.plot(ks, [m.inercia for m in metricas], marker="o")
    izq.set_title("Codo (inercia)")
    izq.set_xlabel("Cantidad de grupos")
    der.plot(ks, [m.silueta for m in metricas], marker="o")
    der.set_title("Silueta")
    der.set_xlabel("Cantidad de grupos")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta)
    plt.close(fig)


def guardar_real_vs_pronostico(
    pronosticos: Pronosticos, ruta: Path, serie: Serie = (1, 1), dias: int = 90
) -> None:
    """Ventas reales contra el pronóstico del bosque para una serie, los primeros días del examen."""
    filas = [f for f, s in enumerate(pronosticos.series) if s == serie][:dias]
    fechas = [pronosticos.fechas[f] for f in filas]
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(fechas, [pronosticos.reales[f] for f in filas], label="Ventas reales")
    ax.plot(
        fechas, [pronosticos.por_metodo["bosque"][f] for f in filas], label="Pronóstico (bosque)"
    )
    ax.set_title(f"Tienda {serie[0]}, producto {serie[1]}: primeros {len(filas)} días del examen")
    ax.set_xticks(fechas[:: max(1, len(fechas) // 6)])
    ax.legend()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta)
    plt.close(fig)
