"""src/application/crecidas/comparar_estaciones.py — Comparación de estaciones."""

from collections.abc import Callable
from dataclasses import dataclass

from src.application.crecidas.construir_dataset import DatasetCrecidas
from src.application.crecidas.puertos import PronosticadorNivelPort

UMBRAL_NIVEL_ALTO_M = 2.0


@dataclass(frozen=True)
class ComparacionEstaciones:
    """Resultados de comparar el uso de una o dos estaciones."""

    horizonte_dias: int
    mae_tigre: float
    mae_dos_estaciones: float
    mejora_mae_porcentaje: float
    rmse_tigre: float
    rmse_dos_estaciones: float
    ejemplos_niveles_altos: int
    mae_tigre_niveles_altos: float
    mae_dos_estaciones_niveles_altos: float


def _mae(reales: list[float], predicciones: list[float]) -> float:
    return sum(
        abs(real - predicho)
        for real, predicho in zip(reales, predicciones, strict=True)
    ) / len(reales)


def _rmse(reales: list[float], predicciones: list[float]) -> float:
    return (
        sum(
            (real - predicho) ** 2
            for real, predicho in zip(reales, predicciones, strict=True)
        ) / len(reales)
    ) ** 0.5


def _mae_niveles_altos(
    reales: list[float],
    predicciones: list[float],
) -> float:
    indices = [
        i for i, valor in enumerate(reales)
        if valor >= UMBRAL_NIVEL_ALTO_M
    ]
    if not indices:
        return float("nan")

    return _mae(
        [reales[i] for i in indices],
        [predicciones[i] for i in indices],
    )


def _obtener_predicciones(
    variables_train: list[list[float]],
    objetivos_train: list[float],
    variables_test: list[list[float]],
    crear_pronosticador: Callable[[], PronosticadorNivelPort],
) -> tuple[list[float], list[float]]:

    """Entrena los modelos de una y dos estaciones."""
    modelo_tigre = crear_pronosticador()
    modelo_tigre.entrenar(
        [fila[::2] for fila in variables_train],
        objetivos_train,
    )
    pred_tigre = modelo_tigre.predecir(
        [fila[::2] for fila in variables_test]
    )

    modelo_dos = crear_pronosticador()
    modelo_dos.entrenar(variables_train, objetivos_train)
    pred_dos = modelo_dos.predecir(variables_test)

    return pred_tigre, pred_dos


def comparar_estaciones(
    dataset: DatasetCrecidas,
    crear_pronosticador: Callable[[], PronosticadorNivelPort],
) -> ComparacionEstaciones:
    """Compara ambos modelos en las mismas fechas de prueba."""
    corte = round(len(dataset.fechas) * 0.8)
    if corte == 0 or corte >= len(dataset.fechas):
        raise ValueError("No hay suficientes datos para evaluar.")

    variables_train = dataset.variables[:corte]
    variables_test = dataset.variables[corte:]
    objetivos_train = dataset.objetivos[:corte]
    objetivos_test = dataset.objetivos[corte:]

    pred_tigre, pred_dos = _obtener_predicciones(
        variables_train,
        objetivos_train,
        variables_test,
        crear_pronosticador,
    )

    mae_tigre = _mae(objetivos_test, pred_tigre)
    mae_dos = _mae(objetivos_test, pred_dos)
    mejora = (
        (mae_tigre - mae_dos) / mae_tigre * 100
        if mae_tigre else 0.0
    )

    return ComparacionEstaciones(
        horizonte_dias=dataset.horizonte_dias,
        mae_tigre=mae_tigre,
        mae_dos_estaciones=mae_dos,
        mejora_mae_porcentaje=mejora,
        rmse_tigre=_rmse(objetivos_test, pred_tigre),
        rmse_dos_estaciones=_rmse(objetivos_test, pred_dos),
        ejemplos_niveles_altos=sum(
            valor >= UMBRAL_NIVEL_ALTO_M for valor in objetivos_test
        ),
        mae_tigre_niveles_altos=_mae_niveles_altos(
            objetivos_test, pred_tigre
        ),
        mae_dos_estaciones_niveles_altos=_mae_niveles_altos(
            objetivos_test, pred_dos
        ),
    )
