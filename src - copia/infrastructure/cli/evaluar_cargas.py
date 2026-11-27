"""src/infrastructure/cli/evaluar_cargas.py — Compara lo identificado con la verdad de un medidor simulado.

Uso:
    ./run.sh evaluate                         # medidor "sintetico"
    ./run.sh evaluate sintetico --umbral 30   # con los mismos parámetros NILM que train
"""

import argparse
from pathlib import Path

from src.application.cargas.dtos.identificar_cargas import IdentificarCargasRequest
from src.application.cargas.use_cases.evaluar_identificacion import EvaluarIdentificacionUseCase
from src.application.cargas.use_cases.identificar_cargas import IdentificarCargasUseCase
from src.infrastructure.cli.entrenar_cargas import (
    PARAMETROS_NILM,
    TODO_EL_RANGO,
    agregar_parametros_nilm,
)
from src.infrastructure.csv.verdad_repository import CsvVerdadRepository
from src.infrastructure.mediciones_factory import get_mediciones
from src.infrastructure.settings.config import describir_nilm, get_settings
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.dbscan_agrupador import DbscanAgrupador


def leer_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evalúa la identificación de cargas contra la verdad conocida."
    )
    parser.add_argument(
        "medidor", nargs="?", default="sintetico", help="medidor simulado (por defecto: sintetico)"
    )
    agregar_parametros_nilm(parser)
    return parser.parse_args()


def main() -> None:
    args = leer_argumentos()
    cambios = {
        var: getattr(args, opcion)
        for opcion, var in PARAMETROS_NILM.items()
        if getattr(args, opcion) is not None
    }
    settings = get_settings().model_copy(update=cambios)
    verdad = CsvVerdadRepository(Path(settings.VERDAD_DIR))
    if args.medidor not in verdad.medidores():
        logger.error(
            "No hay verdad conocida para %s (simulados: %s). Generala con ./run.sh simulate",
            args.medidor, ", ".join(verdad.medidores()) or "ninguno",
        )  # fmt: skip
        return
    identificar = IdentificarCargasUseCase(
        mediciones=get_mediciones(settings),
        agrupador=DbscanAgrupador(),
        umbral_kw=settings.NILM_UMBRAL_KW,
        logger=logger,
        balance_minimo=settings.NILM_BALANCE_MINIMO,
        separacion_minima=settings.NILM_SEPARACION_MINIMA,
        radio_kw=settings.NILM_EPS_KW,
        min_eventos=settings.NILM_MIN_EVENTOS,
    )
    logger.info(describir_nilm(settings))
    desde, hasta = TODO_EL_RANGO
    EvaluarIdentificacionUseCase(identificar, verdad, logger).execute(
        IdentificarCargasRequest(medidor=args.medidor, desde=desde, hasta=hasta)
    )


if __name__ == "__main__":
    main()
