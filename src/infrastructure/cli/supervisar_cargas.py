"""src/infrastructure/cli/supervisar_cargas.py — Entrena un clasificador con la verdad de un medidor simulado.

Uso:
    ./run.sh supervise                          # medidor "sintetico", 70 % para entrenar
    ./run.sh supervise --entrenamiento 0.3      # menos ejemplos etiquetados
    ./run.sh supervise --profundidad 2          # un árbol más chico
"""

import argparse
from pathlib import Path

from src.application.cargas.use_cases.entrenar_clasificador import EntrenarClasificadorUseCase
from src.infrastructure.cli.entrenar_cargas import _entero_positivo
from src.infrastructure.csv.medicion_repository import CsvMedicionRepository
from src.infrastructure.csv.verdad_repository import CsvVerdadRepository
from src.infrastructure.settings.config import get_settings
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.arbol_clasificador import ArbolClasificador


def _fraccion(texto: str) -> float:
    valor = float(texto)
    if not 0 < valor < 1:
        raise argparse.ArgumentTypeError(
            f"tiene que estar entre 0 y 1, sin incluirlos (recibido {texto})"
        )
    return valor


def leer_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aprende las cargas de un medidor simulado a partir de su verdad."
    )
    parser.add_argument(
        "medidor", nargs="?", default="sintetico", help="medidor simulado (por defecto: sintetico)"
    )
    parser.add_argument(
        "--entrenamiento",
        type=_fraccion,
        default=0.7,
        metavar="F",
        help="fracción inicial para entrenar (por defecto: 0.7)",
    )
    parser.add_argument(
        "--profundidad",
        type=_entero_positivo,
        default=6,
        metavar="N",
        help="profundidad máxima del árbol (por defecto: 6)",
    )
    return parser.parse_args()


def main() -> None:
    args = leer_argumentos()
    settings = get_settings()
    verdad = CsvVerdadRepository(Path(settings.VERDAD_DIR))
    if args.medidor not in verdad.medidores():
        logger.error(
            "No hay verdad conocida para %s (simulados: %s). Generala con ./run.sh simulate",
            args.medidor, ", ".join(verdad.medidores()) or "ninguno",
        )  # fmt: skip
        return
    EntrenarClasificadorUseCase(
        mediciones=CsvMedicionRepository(Path(settings.MEDICIONES_CSV_DIR)),
        verdad=verdad,
        clasificador=ArbolClasificador(profundidad=args.profundidad),
        logger=logger,
    ).execute(args.medidor, args.entrenamiento)


if __name__ == "__main__":
    main()
