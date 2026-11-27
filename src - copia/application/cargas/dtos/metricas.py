"""src/application/cargas/dtos/metricas.py — DTOs para observabilidad MLOps."""

from pydantic import BaseModel, ConfigDict, Field


class MetricasClase(BaseModel):
    """Métricas por clase: precision, sensibilidad, F1."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    clase: str = Field(description="Etiqueta de clase")
    precision: float = Field(
        ge=0.0, le=1.0, description="De predichos como esta clase, cuántos lo eran"
    )
    sensibilidad: float = Field(
        ge=0.0, le=1.0, description="De ejemplos reales de esta clase, cuántos se detectaron"
    )
    f1: float = Field(ge=0.0, le=1.0, description="Media armónica de precision y sensibilidad")
    soporte: int = Field(ge=0, description="Cantidad de ejemplos reales de esta clase")


class CeldaMatriz(BaseModel):
    """Una celda de la matriz de confusión: cuántos ejemplos reales de clase X se predijeron como clase Y."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    real: str = Field(description="Clase real del ejemplo")
    predicha: str = Field(description="Clase predicha por el modelo")
    cantidad: int = Field(ge=0, description="Número de ejemplos en esta celda")


class MetricasResponse(BaseModel):
    """Métricas globales de desempeño del modelo supervisado."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    exactitud_global: float = Field(
        ge=0.0, le=1.0, description="Fracción de ejemplos bien clasificados"
    )
    matriz_confusion: list[CeldaMatriz] = Field(
        description="Matriz de confusión: alineación de predicciones vs. reales"
    )
    metricas_por_clase: list[MetricasClase] = Field(
        description="Precision, sensibilidad y F1 de cada clase"
    )
    total_ejemplos: int = Field(ge=0, description="Cantidad de ejemplos en la evaluación")
    f1_macro: float = Field(ge=0.0, le=1.0, description="F1 promedio no ponderado (macro-average)")
    f1_ponderado: float = Field(
        ge=0.0, le=1.0, description="F1 promedio ponderado por soporte de cada clase"
    )
