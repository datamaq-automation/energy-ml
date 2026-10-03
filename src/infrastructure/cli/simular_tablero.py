"""src/infrastructure/cli/simular_tablero.py — Genera un tablero simulado con cargas conocidas.

Uso:
    ./run.sh simulate                         # data/input/sintetico.csv + data/verdad/sintetico.csv
    ./run.sh simulate --semilla 7 --nombre otro
"""

import argparse
from datetime import datetime
from pathlib import Path

from src.domain.cargas.entities import CargaSimulada
from src.domain.cargas.simulacion import simular_tablero
from src.infrastructure.csv.medicion_repository import CsvMedicionRepository
from src.infrastructure.csv.verdad_repository import CsvVerdadRepository
from src.infrastructure.settings.config import get_settings
from src.infrastructure.settings.logger import logger

# Tres equipos elegidos para enseñar: uno fácil (90 kW), uno más chico que el umbral típico (40 kW)
# y uno al nivel del ruido (15 kW = 5 veces el ruido de 3 kW).
CARGAS = [
    CargaSimulada(potencia_kw=90, ciclos_por_dia=18, duracion_min=25),
    CargaSimulada(potencia_kw=40, ciclos_por_dia=6, duracion_min=60),
    CargaSimulada(potencia_kw=15, ciclos_por_dia=30, duracion_min=10),
]
INICIO = datetime(2026, 9, 1)


def leer_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera un tablero simulado con cargas conocidas.")
    parser.add_argument("--nombre", default="sintetico", help="nombre del medidor simulado (por defecto: sintetico)")
    parser.add_argument("--dias", type=int, default=21, help="días a simular (por defecto: 21)")
    parser.add_argument("--ruido", type=float, default=3.0, metavar="KW", help="desvío del ruido (por defecto: 3 kW)")
    parser.add_argument("--semilla", type=int, default=1, help="misma semilla, mismos datos (por defecto: 1)")
    return parser.parse_args()


def main() -> None:
    args = leer_argumentos()
    settings = get_settings()
    descripcion = ", ".join(f"{c.potencia_kw:g} kW ({c.ciclos_por_dia:g}/día)" for c in CARGAS)
    logger.info("Simulando %d días de %s con ruido de %s kW: %s", args.dias, args.nombre, args.ruido, descripcion)
    mediciones, verdad = simular_tablero(CARGAS, args.dias, args.ruido, args.semilla, INICIO)
    CsvMedicionRepository(Path(settings.MEDICIONES_CSV_DIR)).guardar(args.nombre, mediciones)
    CsvVerdadRepository(Path(settings.VERDAD_DIR)).guardar(args.nombre, verdad)


if __name__ == "__main__":
    main()
