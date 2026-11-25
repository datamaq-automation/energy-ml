"""src/infrastructure/cli/analizar_logistica.py — CLI para ejecutar las Tareas A, B y C de logística."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from src.adapters.logistica.controllers.retrasos_controller import RetrasosController
from src.adapters.logistica.gateways.pedidos_csv_gateway import PedidosCsvGateway
from src.adapters.logistica.presenters.retrasos_presenter import RetrasosPresenter
from src.application.logistica.use_cases.analizar_retrasos import AnalizarRetrasosUseCase
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.logistica_modelador import ModeladorRetrasosSklearn


def parse_args() -> argparse.Namespace:
    """Lee argumentos de línea de comandos para el análisis de logística."""
    parser = argparse.ArgumentParser(
        description="Ejecuta el análisis no supervisado (Tarea A), supervisado (Tarea B) y de errores (Tarea C)."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("datos/logistica/pedidos.csv"),
        help="Ruta relativa al archivo CSV de pedidos.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/output"),
        help="Directorio donde se guardarán los gráficos generados.",
    )
    parser.add_argument(
        "--best-k",
        type=int,
        default=5,
        help="Número de clusters k elegido para perfilar en Tarea A.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Profundidad máxima del árbol de decisión en Tarea B.",
    )
    return parser.parse_args()


def main() -> None:
    """Punto de entrada principal del análisis de retrasos logísticos."""
    args = parse_args()
    if not args.csv.exists():
        logger.error("No se encontró el dataset en %s", args.csv)
        return

    logger.info("Cargando y validando pedidos desde %s (cero fuga de datos)...", args.csv)
    controlador = RetrasosController(
        AnalizarRetrasosUseCase(PedidosCsvGateway(args.csv), ModeladorRetrasosSklearn()),
        RetrasosPresenter(),
    )
    _, lineas = controlador.analizar(
        best_k=args.best_k,
        max_depth=args.max_depth,
        destino_graficos=str(args.output_dir),
        ahora=datetime.now(),
    )
    for linea in lineas:
        logger.info("%s", linea)


if __name__ == "__main__":
    main()
