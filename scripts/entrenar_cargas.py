"""scripts/entrenar_cargas.py — Identifica las cargas de data/input/*.csv y las guarda en data/output/.

Uso:
    .venv/bin/python -m scripts.entrenar_cargas                     # todos los medidores, todos los datos
    .venv/bin/python -m scripts.entrenar_cargas planta_2_a          # un medidor
    .venv/bin/python -m scripts.entrenar_cargas planta_2_a --desde 2026-09-15 --hasta 2026-09-22
"""

import argparse
import csv
from datetime import datetime
from pathlib import Path

from src.application.cargas.dtos.identificar_cargas import IdentificarCargasRequest
from src.application.cargas.use_cases.identificar_cargas import IdentificarCargasUseCase
from src.infrastructure.csv.medicion_repository import CsvMedicionRepository
from src.infrastructure.settings.config import describir_nilm, get_settings
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.dbscan_agrupador import DbscanAgrupador

DATA = Path(__file__).resolve().parent.parent / "data"
ENTRADA, SALIDA = DATA / "input", DATA / "output"
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


def guardar(medidor: str, cargas: list[tuple[float, int, int, int]]) -> Path:
    destino = SALIDA / f"cargas_{medidor}.csv"
    with destino.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["potencia_tipica_kw", "encendidos", "apagados", "ciclos"])
        escritor.writerows(cargas)
    return destino


def main() -> None:
    args = leer_argumentos()
    settings = get_settings()
    repositorio = CsvMedicionRepository(ENTRADA)
    caso_de_uso = IdentificarCargasUseCase(
        mediciones=repositorio,
        agrupador=DbscanAgrupador(
            eps_kw=settings.NILM_EPS_KW, min_eventos=settings.NILM_MIN_EVENTOS
        ),
        umbral_kw=settings.NILM_UMBRAL_KW,
        logger=logger,
        balance_minimo=settings.NILM_BALANCE_MINIMO,
    )
    disponibles = repositorio.medidores()
    if not disponibles:
        logger.error("No hay CSV en %s: corré primero la exportación de datos", ENTRADA)
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

    SALIDA.mkdir(parents=True, exist_ok=True)
    logger.info(describir_nilm(settings))
    logger.info(
        "Entrenando con %d de %d medidores de %s",
        len(medidores),
        len(disponibles),
        ENTRADA.relative_to(DATA.parent),
    )
    for medidor in medidores:
        r = caso_de_uso.execute(
            IdentificarCargasRequest(medidor=medidor, desde=args.desde, hasta=args.hasta)
        )
        destino = guardar(
            medidor, [(c.potencia_tipica_kw, c.encendidos, c.apagados, c.ciclos) for c in r.cargas]
        )
        logger.info(
            "%s: %d cargas guardadas en %s",
            medidor,
            len(r.cargas),
            destino.relative_to(DATA.parent),
        )


if __name__ == "__main__":
    main()
