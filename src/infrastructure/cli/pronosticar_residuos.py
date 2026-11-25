"""src/infrastructure/cli/pronosticar_residuos.py — Pronóstico mensual de residuos de Ann Arbor.

Uso: python -m src.infrastructure.cli.pronosticar_residuos [--csv RUTA] [--output-dir RUTA]
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from src.adapters.residuos.controllers.residuos_controller import ResiduosController
from src.adapters.residuos.gateways.residuos_csv_gateway import (
    DEFAULT_DATA,
    DEFAULT_OUTPUT,
    ResiduosCsvGateway,
)
from src.adapters.residuos.presenters.residuos_presenter import ResiduosPresenter
from src.application.residuos.dtos.pronosticar_residuos_response import (
    PronosticarResiduosResponse,
)
from src.application.residuos.use_cases.pronosticar_residuos import PronosticarResiduosUseCase
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.residuos_modelador import PronosticadorResiduosSklearn


def pronosticar(csv_path: Path, output_dir: Path) -> PronosticarResiduosResponse:
    """Arma las dependencias, corre las tres etapas, guarda los CSV y registra el reporte."""
    controlador = ResiduosController(
        PronosticarResiduosUseCase(
            ResiduosCsvGateway(csv_path, output_dir), PronosticadorResiduosSklearn()
        ),
        ResiduosPresenter(),
    )
    respuesta, lineas = controlador.pronosticar(guardar_resultados=True, ahora=datetime.now())
    for linea in lineas:
        logger.info("%s", linea)
    return respuesta


def main() -> None:
    """Lee los argumentos de línea de comandos y ejecuta el pronóstico."""
    parser = argparse.ArgumentParser(description="Pronóstico mensual de residuos de Ann Arbor.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_DATA, help="Ruta al CSV original.")
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT, help="Directorio de resultados."
    )
    args = parser.parse_args()
    pronosticar(args.csv, args.output_dir)


if __name__ == "__main__":
    main()
