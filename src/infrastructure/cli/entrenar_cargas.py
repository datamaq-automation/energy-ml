"""src/infrastructure/cli/entrenar_cargas.py — Identifica las cargas de data/input/*.csv y las guarda en data/output/.

Uso:
    ./run.sh train                                   # todos los medidores, todos los datos
    ./run.sh train planta_2_a                        # un medidor
    ./run.sh train planta_2_a --desde 2026-09-15 --hasta 2026-09-22
"""

import argparse
from datetime import datetime
from pathlib import Path

from src.application.cargas.dtos.identificar_cargas import IdentificarCargasRequest
from src.application.cargas.use_cases.identificar_cargas import IdentificarCargasUseCase
from src.domain.cargas.entities import Carga
from src.domain.cargas.repositories import CargaRepository
from src.infrastructure.csv.carga_repository import CsvCargaRepository
from src.infrastructure.csv.medicion_repository import CsvMedicionRepository
from src.infrastructure.settings.config import describir_nilm, get_settings
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.dbscan_agrupador import DbscanAgrupador

TODO_EL_RANGO = (datetime(2000, 1, 1), datetime(2100, 1, 1))


def leer_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Identifica cargas (NILM) en los CSV de data/input/."
    )
    parser.add_argument(
        "medidores", nargs="*", help="nombres de CSV sin extensión (por defecto: todos)"
    )
    parser.add_argument(
        "--desde", type=datetime.fromisoformat, default=TODO_EL_RANGO[0], help="ej. 2026-09-15"
    )
    parser.add_argument(
        "--hasta", type=datetime.fromisoformat, default=TODO_EL_RANGO[1], help="ej. 2026-09-22"
    )
    return parser.parse_args()


def main() -> None:
    args = leer_argumentos()
    settings = get_settings()
    entrada, salida = Path(settings.MEDICIONES_CSV_DIR), Path(settings.RESULTADOS_DIR)
    repositorio = CsvMedicionRepository(entrada)
    resultados: CargaRepository = CsvCargaRepository(salida)
    caso_de_uso = IdentificarCargasUseCase(
        mediciones=repositorio,
        agrupador=DbscanAgrupador(min_eventos=settings.NILM_MIN_EVENTOS),
        umbral_kw=settings.NILM_UMBRAL_KW,
        logger=logger,
        balance_minimo=settings.NILM_BALANCE_MINIMO,
        separacion_minima=settings.NILM_SEPARACION_MINIMA,
        radio_kw=settings.NILM_EPS_KW,
    )
    disponibles = repositorio.medidores()
    if not disponibles:
        logger.error("No hay CSV en %s: corré primero la exportación de datos", entrada)
        return
    desconocidos = [m for m in args.medidores if m not in disponibles]
    if desconocidos:
        logger.error(
            "Medidores desconocidos: %s (disponibles: %s)",
            ", ".join(desconocidos),
            ", ".join(disponibles),
        )
        return
    medidores = args.medidores or disponibles

    logger.info(describir_nilm(settings))
    logger.info(
        "Entrenando con %d de %d medidores de %s",
        len(medidores),
        len(disponibles),
        entrada,
    )
    for medidor in medidores:
        r = caso_de_uso.execute(
            IdentificarCargasRequest(medidor=medidor, desde=args.desde, hasta=args.hasta)
        )
        resultados.guardar(
            medidor, [Carga(c.potencia_tipica_kw, c.encendidos, c.apagados) for c in r.cargas]
        )


if __name__ == "__main__":
    main()
