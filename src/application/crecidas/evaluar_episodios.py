"""src/application/crecidas/evaluar_episodios.py — Evaluación de episodios."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from src.application.crecidas.construir_dataset import DatasetCrecidas
from src.application.crecidas.puertos import PronosticadorNivelPort

UMBRAL_EPISODIO_M = 2.0


@dataclass(frozen=True)
class ResultadoEpisodios:
    """Resultados de detección de episodios para modelo y persistencia."""

    horizonte_dias: int
    episodios_reales: int
    anticipados_modelo: int
    anticipados_persistencia: int
    no_detectados_modelo: int
    sensibilidad_modelo: float
    falsos_positivos_modelo: int
    falsos_positivos_persistencia: int


def _obtener_indices_entrenamiento(
    dataset: DatasetCrecidas,
    corte: int,
) -> list[int]:
    """Excluye ejemplos cuyos objetivos se solapan con la prueba."""
    fecha_inicio = dataset.fechas[corte]
    return [
        i for i in range(corte)
        if dataset.fechas[i] + timedelta(days=dataset.horizonte_dias)
        < fecha_inicio
    ]


def _identificar_inicios(
    fechas: list[date],
    niveles_tigre: dict[date, float],
) -> list[date]:
    """Identifica los días en que comienza un episodio de nivel alto."""
    return [
        dia for dia in fechas
        if dia - timedelta(days=1) in niveles_tigre
        and niveles_tigre.get(dia, -1) >= UMBRAL_EPISODIO_M
        and niveles_tigre[dia - timedelta(days=1)] < UMBRAL_EPISODIO_M
    ]


def _contar_anticipados(
    inicios: list[date],
    predicciones: dict[date, float],
) -> int:
    """Cuenta los episodios anticipados por el predictor."""
    return sum(
        predicciones[dia] >= UMBRAL_EPISODIO_M
        for dia in inicios
    )


def _contar_falsos_positivos(
    fechas: list[date],
    predicciones: dict[date, float],
    reales: dict[date, float],
) -> int:
    """Cuenta días pronosticados como altos que no fueron altos."""
    return sum(
        predicciones[dia] >= UMBRAL_EPISODIO_M
        and reales[dia] < UMBRAL_EPISODIO_M
        for dia in fechas
    )


def _crear_mapa_predicciones(
    fechas: list[date],
    predicciones: list[float],
    persistencia: list[float],
    reales: list[float],
) -> tuple[dict[date, float], dict[date, float], dict[date, float]]:
    """Asocia predicciones y valores reales con sus fechas objetivo."""
    return (
        dict(zip(fechas, predicciones, strict=True)),
        dict(zip(fechas, persistencia, strict=True)),
        dict(zip(fechas, reales, strict=True)),
    )


def evaluar_episodios(
    dataset: DatasetCrecidas,
    niveles_tigre: dict[date, float],
    crear_pronosticador: Callable[[], PronosticadorNivelPort],
    fraccion_entrenamiento: float = 0.8,
) -> ResultadoEpisodios:
    """Evalúa la anticipación de episodios con separación temporal."""
    if not 0 < fraccion_entrenamiento < 1:
        raise ValueError("La fracción debe estar entre 0 y 1.")
    corte = round(len(dataset.fechas) * fraccion_entrenamiento)
    if corte == 0 or corte >= len(dataset.fechas):
        raise ValueError("No hay suficientes datos para evaluar.")
    indices = _obtener_indices_entrenamiento(dataset, corte)
    if not indices:
        raise ValueError("No hay suficientes datos de entrenamiento.")
    modelo = crear_pronosticador()
    modelo.entrenar(
        [dataset.variables[i] for i in indices],
        [dataset.objetivos[i] for i in indices],
    )
    fechas_test = dataset.fechas[corte:]
    fechas_objetivo = [
        fecha + timedelta(days=dataset.horizonte_dias)
        for fecha in fechas_test
    ]
    variables_test = dataset.variables[corte:]
    reales_test = dataset.objetivos[corte:]
    predicciones = modelo.predecir(variables_test)
    persistencia = [fila[0] for fila in variables_test]
    mapa_modelo, mapa_persistencia, mapa_reales = _crear_mapa_predicciones(
        fechas_objetivo, predicciones, persistencia, reales_test
    )
    inicios = _identificar_inicios(sorted(mapa_reales), niveles_tigre)
    anticipados = _contar_anticipados(inicios, mapa_modelo)
    anticipados_persistencia = _contar_anticipados(inicios, mapa_persistencia)
    return ResultadoEpisodios(
        horizonte_dias=dataset.horizonte_dias,
        episodios_reales=len(inicios),
        anticipados_modelo=anticipados,
        anticipados_persistencia=anticipados_persistencia,
        no_detectados_modelo=len(inicios) - anticipados,
        sensibilidad_modelo=anticipados / len(inicios) if inicios else 0.0,
        falsos_positivos_modelo=_contar_falsos_positivos(
            fechas_objetivo, mapa_modelo, mapa_reales
        ),
        falsos_positivos_persistencia=_contar_falsos_positivos(
            fechas_objetivo, mapa_persistencia, mapa_reales
        ),
    )
