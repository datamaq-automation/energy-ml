"""src/application/medioambiente/dtos/analizar_episodios_request.py — Entrada del caso de uso."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AnalizarEpisodiosRequest(BaseModel):
    """Qué corrida identificar y dónde guardar los gráficos de la Tarea A."""

    model_config = ConfigDict(frozen=True)

    id_informe: str = Field(min_length=1, description="Identidad de la corrida del análisis.")
    destino_graficos: str = Field(
        default="docs/medioambiente/imagenes",
        description="Carpeta donde se guardan los gráficos de codo y silueta.",
    )
