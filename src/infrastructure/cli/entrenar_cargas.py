"""src/infrastructure/cli/entrenar_cargas.py — Identifica las cargas de data/input/*.csv y las guarda en data/output/.

Uso:
    ./run.sh train                                   # todos los medidores, todos los datos
    ./run.sh train planta_2_a                        # un medidor
    ./run.sh train planta_2_a --desde 2026-09-15 --hasta 2026-09-22
    ./run.sh train planta_2_b --umbral 60                # fija un parámetro (el resto sigue automático)
    ./run.sh train --help                                # todas las opciones
"""

import argparse
from datetime import datetime
from pathlib import Path

from src.application.cargas.dtos.identificar_cargas import IdentificarCargasRequest
from src.application.cargas.use_cases.identificar_cargas import IdentificarCargasUseCase
from src.domain.cargas.entities import Carga
from src.domain.cargas.repositories import CargaRepository
from src.infrastructure.csv.carga_repository import CsvCargaRepository
from src.infrastructure.mediciones_factory import get_mediciones
from src.infrastructure.settings.config import describir_nilm, get_settings
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.dbscan_agrupador import DbscanAgrupador

TODO_EL_RANGO = (datetime(2000, 1, 1), datetime(2100, 1, 1))

# Opción de la CLI → variable de Settings. Lo que se pasa por argumento tiene prioridad.
PARAMETROS_NILM = {
    "umbral": "NILM_UMBRAL_KW",
    "radio": "NILM_EPS_KW",
    "min_eventos": "NILM_MIN_EVENTOS",
    "separacion_minima": "NILM_SEPARACION_MINIMA",
    "balance_minimo": "NILM_BALANCE_MINIMO",
}


def _positivo(texto: str) -> float:
    valor = float(texto)
    if valor <= 0:
        raise argparse.ArgumentTypeError(f"tiene que ser mayor que 0 (recibido {texto})")
    return valor


def _entero_positivo(texto: str) -> int:
    valor = int(texto)
    if valor < 1:
        raise argparse.ArgumentTypeError(f"tiene que ser al menos 1 (recibido {texto})")
    return valor


def _proporcion(texto: str) -> float:
    valor = float(texto)
    if not 0 <= valor <= 1:
        raise argparse.ArgumentTypeError(f"tiene que estar entre 0 y 1 (recibido {texto})")
    return valor


def agregar_parametros_nilm(parser: argparse.ArgumentParser) -> None:
    """Opciones para fijar los parámetros NILM (las comparten train y evaluate)."""
    nilm = parser.add_argument_group(
        "parámetros NILM",
        "Sin estas opciones se usa config.py (umbral, radio y mínimo son automáticos). Criterios para elegirlos: docs/guia-docente.md, §6 y §7.",
    )
    nilm.add_argument(
        "--umbral", type=_positivo, metavar="KW", help="umbral |ΔP| fijo (por defecto: Otsu)"
    )
    nilm.add_argument(
        "--radio",
        type=_positivo,
        metavar="KW",
        help="radio de DBSCAN fijo (por defecto: F–D / 2 × ruido)",
    )
    nilm.add_argument(
        "--min-eventos",
        type=_entero_positivo,
        metavar="N",
        help="eventos mínimos por carga (por defecto: uno por día)",
    )
    nilm.add_argument(
        "--separacion-minima",
        type=_proporcion,
        metavar="η",
        help="η mínimo para confiar en el umbral (0 a 1)",
    )
    nilm.add_argument(
        "--balance-minimo",
        type=_proporcion,
        metavar="P",
        help="proporción ciclos/mayor para ser ON/OFF (0 a 1)",
    )


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
    entrada, salida = Path(settings.MEDICIONES_CSV_DIR), Path(settings.RESULTADOS_DIR)
    repositorio = get_mediciones(settings)
    resultados: CargaRepository = CsvCargaRepository(salida)
    caso_de_uso = IdentificarCargasUseCase(
        mediciones=repositorio,
        agrupador=DbscanAgrupador(),
        umbral_kw=settings.NILM_UMBRAL_KW,
        logger=logger,
        balance_minimo=settings.NILM_BALANCE_MINIMO,
        separacion_minima=settings.NILM_SEPARACION_MINIMA,
        radio_kw=settings.NILM_EPS_KW,
        min_eventos=settings.NILM_MIN_EVENTOS,
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
