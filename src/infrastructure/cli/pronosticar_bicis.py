"""src/infrastructure/cli/pronosticar_bicis.py — Ejecuta la comparación temporal de Ecobici."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from src.adapters.bicis.controllers.pronosticos_controller import PronosticosController
from src.adapters.bicis.gateways.repositorio_recorridos_gateway import (
    RepositorioRecorridosBicis,
)
from src.adapters.bicis.presenters.pronosticos_presenter import PronosticosPresenter
from src.application.bicis.dtos.evaluar_pronosticos_response import EvaluarPronosticosResponse
from src.application.bicis.use_cases.evaluar_pronosticos import EvaluarPronosticosUseCase
from src.application.bicis.use_cases.preparar_pronosticos import PrepararPronosticosUseCase
from src.infrastructure.bicis.descargar_datasets import DIRECTORIO_DATOS, descargar_datasets
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.bicis_modelador import BosqueAleatorioPronosticos

DESDE: date = date(2024, 1, 1)
HASTA: date = date(2025, 12, 31)


def leer_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evalúa pronósticos diarios de bicicletas públicas."
    )
    parser.add_argument(
        "--directorio-datos",
        type=Path,
        default=DIRECTORIO_DATOS,
        help="Directorio con los ZIP oficiales (por defecto: datos/bicis).",
    )
    return parser.parse_args()


def ejecutar(directorio_datos: Path = DIRECTORIO_DATOS) -> EvaluarPronosticosResponse:
    """Compone las capas, ejecuta el controller e informa el reporte."""
    archivos = descargar_datasets(directorio_datos)
    repositorio = RepositorioRecorridosBicis(archivos)
    preparador = PrepararPronosticosUseCase(repositorio)
    caso_de_uso = EvaluarPronosticosUseCase(preparador, BosqueAleatorioPronosticos())
    controller = PronosticosController(caso_de_uso, PronosticosPresenter())
    respuesta, lineas = controller.evaluar(DESDE, HASTA)
    calidad = repositorio.calidad
    logger.info(
        "Control de recorridos: %d filas, %d duplicados descartados (%d conflictivos), "
        "%d IDs vacíos, %d fechas inválidas y %d filas malformadas",
        calidad.filas_leidas,
        calidad.viajes_duplicados,
        calidad.duplicados_conflictivos,
        calidad.ids_ausentes,
        calidad.fechas_invalidas,
        calidad.filas_malformadas,
    )
    for linea in lineas:
        logger.info(linea)
    _informar_fechas_faltantes(respuesta.dias_faltantes)
    return respuesta


def _informar_fechas_faltantes(fechas: tuple[date, ...]) -> None:
    for anio in (2024, 2025):
        faltantes = tuple(fecha for fecha in fechas if fecha.year == anio)
        if faltantes:
            mostradas = ", ".join(fecha.isoformat() for fecha in faltantes[:10])
            restantes = len(faltantes) - min(len(faltantes), 10)
            sufijo = f" y {restantes} más" if restantes else ""
            logger.warning("Fechas sin registros en %d: %s%s", anio, mostradas, sufijo)


def main() -> None:
    args = leer_argumentos()
    ejecutar(args.directorio_datos)


if __name__ == "__main__":
    main()
