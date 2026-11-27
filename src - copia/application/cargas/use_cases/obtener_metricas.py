"""src/application/cargas/use_cases/obtener_metricas.py — Caso de uso para observabilidad MLOps."""

from src.application.cargas.dtos.metricas import (
    CeldaMatriz,
    MetricasClase,
    MetricasResponse,
)
from src.domain.cargas.entities import MatrizConfusion


def _calcular_metricas_por_clase(
    matriz: MatrizConfusion,
) -> tuple[list[MetricasClase], list[float], list[int]]:
    """Calcula precision, sensibilidad y F1 para cada clase."""
    metricas: list[MetricasClase] = []
    f1_scores: list[float] = []
    soportes: list[int] = []

    for clase in matriz.clases:
        prec = matriz.precision(clase)
        sens = matriz.sensibilidad(clase)
        f1 = 2 * (prec * sens) / (prec + sens) if (prec + sens) > 0 else 0.0
        soporte = sum(matriz.celdas[clase].values())

        metricas.append(
            MetricasClase(
                clase=clase,
                precision=round(prec, 4),
                sensibilidad=round(sens, 4),
                f1=round(f1, 4),
                soporte=soporte,
            )
        )
        f1_scores.append(f1)
        soportes.append(soporte)

    return metricas, f1_scores, soportes


def _serializar_matriz_confusión(matriz: MatrizConfusion) -> list[CeldaMatriz]:
    """Serializa la matriz de confusión a lista de celdas."""
    return [
        CeldaMatriz(real=real, predicha=predicha, cantidad=matriz.celdas[real][predicha])
        for real in matriz.clases
        for predicha in matriz.clases
    ]


def _calcular_f1_promedio(f1_scores: list[float], soportes: list[int]) -> tuple[float, float]:
    """Calcula F1 macro y ponderado."""
    f1_macro = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
    f1_ponderado = (
        sum(f * s for f, s in zip(f1_scores, soportes, strict=False)) / sum(soportes)
        if sum(soportes) > 0
        else 0.0
    )
    return f1_macro, f1_ponderado


class ObtenerMetricasUseCase:
    """Extrae métricas de desempeño del modelo de clasificación supervisado."""

    def __init__(self, matriz_confusion_repo: "MatrizConfusionRepository") -> None:
        self._repo = matriz_confusion_repo

    def execute(self) -> MetricasResponse:
        """Calcula y retorna las métricas globales y por clase del último entrenamiento."""
        matriz = self._repo.obtener_ultima()
        if not matriz:
            return MetricasResponse(
                exactitud_global=0.0,
                matriz_confusion=[],
                metricas_por_clase=[],
                total_ejemplos=0,
                f1_macro=0.0,
                f1_ponderado=0.0,
            )

        metricas_clase, f1_scores, soportes = _calcular_metricas_por_clase(matriz)
        matriz_list = _serializar_matriz_confusión(matriz)
        f1_macro, f1_ponderado = _calcular_f1_promedio(f1_scores, soportes)

        return MetricasResponse(
            exactitud_global=round(matriz.exactitud, 4),
            matriz_confusion=matriz_list,
            metricas_por_clase=metricas_clase,
            total_ejemplos=matriz.total,
            f1_macro=round(f1_macro, 4),
            f1_ponderado=round(f1_ponderado, 4),
        )


class MatrizConfusionRepository:
    """Repositorio en memoria de la última matriz de confusión calculada."""

    def __init__(self) -> None:
        self._matriz: MatrizConfusion | None = None

    def guardar(self, matriz: MatrizConfusion) -> None:
        """Registra la matriz de confusión más reciente."""
        self._matriz = matriz

    def obtener_ultima(self) -> MatrizConfusion | None:
        """Retorna la última matriz registrada, o None si no hay."""
        return self._matriz
