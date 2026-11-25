"""src/application/logistica/dtos/analizar_retrasos_request.py — Entrada del caso de uso."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AnalizarRetrasosRequest(BaseModel):
    """Parámetros de la corrida: k a perfilar, profundidad del árbol y segmento de la Tarea C."""

    model_config = ConfigDict(frozen=True)

    id_informe: str = Field(min_length=1, description="Identidad de la corrida del análisis.")
    best_k: int = Field(default=5, ge=2, description="k elegido para perfilar en la Tarea A.")
    max_depth: int = Field(default=5, ge=1, description="Profundidad del árbol en la Tarea B.")
    segmento: str = Field(default="Shipping Mode", description="Columna para desglosar errores.")
    destino_graficos: str = Field(default="data/output", description="Carpeta de los gráficos.")
