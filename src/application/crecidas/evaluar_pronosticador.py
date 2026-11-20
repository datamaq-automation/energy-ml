"""src/application/crecidas/evaluar_pronosticador.py — Evaluación temporal."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from src.application.crecidas.construir_dataset import DatasetCrecidas
from src.application.crecidas.puertos import PronosticadorNivelPort

UMBRAL_ANALISIS_M = 2.0
UMBRAL_ALERTA_TIGRE_M = 3.30


@dataclass(frozen=True)
class ResultadoEvaluacion:
    """Métricas generales y específicas de niveles elevados."""

    horizonte_dias: int
    ejemplos_entrenamiento: int
    ejemplos_prueba: int
    mae_modelo: float
    rmse_modelo: float
    mae_persistencia: float
    rmse_persistencia: float
    mejora_mae_porcentaje: float
    mae_niveles_altos: float
    ejemplos_niveles_altos: int
    mae_alerta: float
    ejemplos_alerta: int
    alertas_subestimadas: int
    error_maximo: float
    fecha_error_maximo: str


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


def _indices_entrenamiento(
    dataset: DatasetCrecidas,
    corte: int,
) -> list[int]:
    """Evita que los objetivos de entrenamiento se solapen con la prueba."""
    fecha_inicio_prueba = dataset.fechas[corte]
    return [
        i
        for i in range(corte)
        if dataset.fechas[i] + timedelta(days=dataset.horizonte_dias)
        < fecha_inicio_prueba
    ]


def _mae_filtrado(
    reales: list[float],
    predicciones: list[float],
    indices: list[int],
) -> float:
    """Calcula el MAE para un subconjunto de ejemplos."""
    if not indices:
        return float("nan")

    return _mae(
        [reales[i] for i in indices],
        [predicciones[i] for i in indices],
    )


class EvaluarPronosticadorUseCase:
    """Entrena y evalúa un modelo con separación cronológica."""

    def execute(
        self,
        dataset: DatasetCrecidas,
        crear_pronosticador: Callable[[], PronosticadorNivelPort],
        fraccion_entrenamiento: float = 0.8,
    ) -> ResultadoEvaluacion:
        """Evalúa el predictor frente a la persistencia."""
        if not 0 < fraccion_entrenamiento < 1:
            raise ValueError("La fracción debe estar entre 0 y 1.")

        corte = round(len(dataset.fechas) * fraccion_entrenamiento)
        if corte == 0 or corte >= len(dataset.fechas):
            raise ValueError("No hay suficientes ejemplos para evaluar.")

        indices_train = _indices_entrenamiento(dataset, corte)
        if not indices_train:
            raise ValueError("No hay suficientes datos de entrenamiento.")

        modelo = crear_pronosticador()
        modelo.entrenar(
            [dataset.variables[i] for i in indices_train],
            [dataset.objetivos[i] for i in indices_train],
        )

        variables_test = dataset.variables[corte:]
        reales = dataset.objetivos[corte:]
        fechas_test = dataset.fechas[corte:]
        predicciones = modelo.predecir(variables_test)
        persistencia = [fila[0] for fila in variables_test]

        return self._crear_resultado(
            dataset,
            len(indices_train),
            reales,
            predicciones,
            persistencia,
            fechas_test,
        )

    @staticmethod
    def _crear_resultado(
        dataset: DatasetCrecidas,
        ejemplos_entrenamiento: int,
        reales: list[float],
        predicciones: list[float],
        persistencia: list[float],
        fechas_test: list,
    ) -> ResultadoEvaluacion:
        """Calcula las métricas y construye el resultado de evaluación."""
        mae_modelo = _mae(reales, predicciones)
        mae_persistencia = _mae(reales, persistencia)

        indices_altos = [
            i for i, valor in enumerate(reales)
            if valor >= UMBRAL_ANALISIS_M
        ]
        indices_alerta = [
            i for i, valor in enumerate(reales)
            if valor >= UMBRAL_ALERTA_TIGRE_M
        ]

        errores = [
            abs(real - predicho)
            for real, predicho in zip(reales, predicciones, strict=True)
        ]
        indice_maximo = max(range(len(errores)), key=errores.__getitem__)

        return ResultadoEvaluacion(
            horizonte_dias=dataset.horizonte_dias,
            ejemplos_entrenamiento=ejemplos_entrenamiento,
            ejemplos_prueba=len(reales),
            mae_modelo=mae_modelo,
            rmse_modelo=_rmse(reales, predicciones),
            mae_persistencia=mae_persistencia,
            rmse_persistencia=_rmse(reales, persistencia),
            mejora_mae_porcentaje=(
                (mae_persistencia - mae_modelo) / mae_persistencia * 100
                if mae_persistencia
                else 0.0
            ),
            mae_niveles_altos=_mae_filtrado(
                reales, predicciones, indices_altos
            ),
            ejemplos_niveles_altos=len(indices_altos),
            mae_alerta=_mae_filtrado(reales, predicciones, indices_alerta),
            ejemplos_alerta=len(indices_alerta),
            alertas_subestimadas=sum(
                predicciones[i] < reales[i] for i in indices_alerta
            ),
            error_maximo=errores[indice_maximo],
            fecha_error_maximo=fechas_test[indice_maximo].isoformat(),
        )
