"""src/infrastructure/cli/analizar_ventas.py — CLI para las Tareas A, B y C del pronóstico de ventas (issue #2)."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.adapters.ventas.controlador import ControladorVentas
from src.application.ventas.use_cases import AgruparSeriesUseCase, PronosticarDemandaUseCase
from src.domain.ventas.modelos import K_ELEGIDO
from src.infrastructure.csv.venta_repository import CsvVentaRepository
from src.infrastructure.graficos.ventas import guardar_codo_silueta, guardar_real_vs_pronostico
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.ventas_agrupador import KMeansAgrupadorVentas
from src.infrastructure.sklearn.ventas_pronosticador import SklearnPronosticadorVentas


def parse_args() -> argparse.Namespace:
    """Lee los argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(description="Agrupa series de ventas y compara pronósticos.")
    parser.add_argument("--csv", type=Path, default=Path("datos/ventas/demanda.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/output"))
    parser.add_argument("--k", type=int, default=K_ELEGIDO, help="Cantidad de grupos (Tarea A).")
    parser.add_argument("--arboles", type=int, default=200, help="Árboles del bosque (Tarea B).")
    return parser.parse_args()


def main() -> None:
    """Arma las piezas, corre las tres tareas y guarda los gráficos en --output-dir."""
    args = parse_args()
    if not args.csv.exists():
        logger.error("No se encontró el dataset en %s (ver issue #2 para descargarlo).", args.csv)
        return

    fuente = CsvVentaRepository(args.csv)
    controlador = ControladorVentas(
        AgruparSeriesUseCase(fuente, KMeansAgrupadorVentas()),
        PronosticarDemandaUseCase(fuente, SklearnPronosticadorVentas(arboles=args.arboles)),
    )
    reporte = controlador.analizar(k_elegido=args.k)
    for renglon in reporte.renglones:
        logger.info(renglon)

    codo = args.output_dir / "ventas_codo_silueta.png"
    guardar_codo_silueta(reporte.agrupamiento.metricas, codo)
    real = args.output_dir / "ventas_real_vs_pronostico.png"
    guardar_real_vs_pronostico(reporte.pronostico.pronosticos, real)
    logger.info("Gráficos guardados en %s y %s", codo, real)


if __name__ == "__main__":
    main()
