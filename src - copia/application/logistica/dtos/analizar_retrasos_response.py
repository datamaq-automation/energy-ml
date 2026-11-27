"""src/application/logistica/dtos/analizar_retrasos_response.py — Salida del caso de uso."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PerfilGrupoDTO(BaseModel):
    """Un grupo de la Tarea A con su lectura de negocio."""

    model_config = ConfigDict(frozen=True)

    cluster_id: int
    order_count: int
    business_description: str
    late_delivery_rate: float


class MetricasModeloDTO(BaseModel):
    """Métricas de un modelo de la Tarea B sobre test."""

    model_config = ConfigDict(frozen=True)

    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    confusion_matrix: list[list[int]]


class SegmentoDTO(BaseModel):
    """Recall del árbol en un segmento (Tarea C)."""

    model_config = ConfigDict(frozen=True)

    segment_type: str
    segment_value: str
    order_count: int
    actual_late_rate: float
    recall: float


class AnalizarRetrasosResponse(BaseModel):
    """Resultados de las Tareas A, B y C listos para presentar."""

    model_config = ConfigDict(frozen=True)

    id_informe: str
    pedidos: int
    ks_evaluados: list[int]
    perfiles: list[PerfilGrupoDTO]
    modelos: list[MetricasModeloDTO]
    importancias: list[tuple[str, float]]
    segmentos: list[SegmentoDTO]
    graficos: list[str]
    eventos: list[str]
