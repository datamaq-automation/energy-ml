"""src/infrastructure/cli/pronosticar_bicis.py — Ejecuta la comparación temporal de Ecobici."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from src.adapters.bicis.repositorio_recorridos import RepositorioRecorridosBicis
from src.application.bicis.use_cases.preparar_pronosticos import PrepararPronosticosUseCase
from src.infrastructure.bicis.descargar_datasets import DIRECTORIO_DATOS, descargar_datasets
from src.infrastructure.bicis.evaluar_pronosticos import (
    ResultadoEvaluacionPronosticos,
    evaluar_2024_2025,
)
from src.infrastructure.settings.logger import logger

DESDE: date = date(2024, 1, 1)
HASTA: date = date(2025, 12, 31)


def ejecutar(directorio_datos: Path = DIRECTORIO_DATOS) -> ResultadoEvaluacionPronosticos:
    """Descarga si hace falta, prepara muestras y muestra métricas sin escribir resultados."""
    archivos = descargar_datasets(directorio_datos)
    repositorio = RepositorioRecorridosBicis(archivos)
    preparacion = PrepararPronosticosUseCase(repositorio).execute(DESDE, HASTA)
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
    _informar_cobertura(preparacion.dias_faltantes, preparacion.dias_sin_rezagos)
    resultado = evaluar_2024_2025(preparacion.muestras)
    _informar_metricas(resultado)
    return resultado


def _informar_cobertura(faltantes: tuple[date, ...], sin_rezagos: tuple[date, ...]) -> None:
    for anio in (2024, 2025):
        faltan = tuple(fecha for fecha in faltantes if fecha.year == anio)
        sin_historia = tuple(fecha for fecha in sin_rezagos if fecha.year == anio)
        logger.info(
            "%d: %d días sin registros, %d días observados sin rezagos completos",
            anio,
            len(faltan),
            len(sin_historia),
        )
        if faltan:
            logger.warning("Fechas sin registros en %d: %s", anio, _listar_fechas(faltan))


def _listar_fechas(fechas: tuple[date, ...]) -> str:
    mostradas = ", ".join(fecha.isoformat() for fecha in fechas[:10])
    restantes = len(fechas) - min(len(fechas), 10)
    return mostradas if restantes == 0 else f"{mostradas} y {restantes} más"


def _informar_metricas(resultado: ResultadoEvaluacionPronosticos) -> None:
    logger.info(
        "Muestras: %d días de entrenamiento (2024), %d de prueba (2025)",
        resultado.dias_entrenamiento,
        resultado.dias_prueba,
    )
    logger.info("%-34s %12s %12s", "Método", "MAE (viajes)", "RMSE (viajes)")
    for metrica in (resultado.linea_base, resultado.bosque_aleatorio):
        logger.info("%-34s %12.2f %12.2f", metrica.nombre, metrica.mae, metrica.rmse)


def main() -> None:
    ejecutar()


if __name__ == "__main__":
    main()
