"""src/application/medioambiente/dtos/analizar_episodios_response.py — Salida del caso de uso."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DiagnosticoKDTO(BaseModel):
    """Una fila del diagnóstico de K-means."""

    model_config = ConfigDict(frozen=True)

    k: int
    inercia: float
    silueta: float


class PerfilGrupoDTO(BaseModel):
    """Medias meteorológicas y proporción de episodios de un grupo."""

    model_config = ConfigDict(frozen=True)

    grupo: int
    horas: int
    temperatura_media: float
    humedad_relativa_media: float
    humedad_absoluta_media: float
    proporcion_episodio: float


class MetricasModeloDTO(BaseModel):
    """Métricas de un modelo en una partición (`split` = aleatorio o temporal)."""

    model_config = ConfigDict(frozen=True)

    modelo: str
    split: str
    accuracy: float
    precision: float
    recall: float
    f1: float


class CambioDistribucionDTO(BaseModel):
    """Comparación de una feature entre train y test temporales."""

    model_config = ConfigDict(frozen=True)

    feature: str
    media_train: float
    media_test: float
    desvio_estandarizado: float
    cambio: bool


class AnalizarEpisodiosResponse(BaseModel):
    """Resultados de las Tareas A, B y C listos para presentar."""

    model_config = ConfigDict(frozen=True)

    id_informe: str
    filas_cargadas: int
    mejor_k: int
    diagnosticos: list[DiagnosticoKDTO]
    grupos: list[PerfilGrupoDTO]
    metricas: list[MetricasModeloDTO]
    mejor_modelo: str
    matriz_confusion: list[list[int]]
    cambios: list[CambioDistribucionDTO]
    features_con_cambio: list[str]
    graficos: list[str]
    eventos: list[str]
