"""src/application/cargas/dtos/maquinas_inferidas.py — DTOs para máquinas inferidas por NILM."""

from datetime import datetime

from pydantic import BaseModel, Field


class MaquinaInferidaDTO(BaseModel):
    """Una máquina/carga individual inferida por NILM."""

    id: str = Field(min_length=1, examples=["carga_001"])
    nombre: str | None = Field(
        default=None,
        examples=["Bomba A", None],
        description="Nombre legible. Si None, usar 'Carga sin nombre'",
    )
    potencia_tipica_kw: float = Field(
        gt=0, examples=[92.5], description="Potencia típica en kilovatios"
    )
    confianza: str = Field(
        examples=["alta"],
        pattern="^(alta|media|baja)$",
        description="Nivel de confianza en la detección: alta, media o baja",
    )
    encendidos: int = Field(ge=0, examples=[412], description="Total de encendidos detectados")
    apagados: int = Field(ge=0, examples=[380], description="Total de apagados detectados")
    ciclos_por_dia: float | None = Field(
        default=None,
        examples=[24.5, None],
        description="Promedio de ciclos por día. None si rango < 1 día",
    )
    dispersion_kw: float = Field(
        ge=0.0,
        examples=[3.2],
        description="Desvío estándar de |ΔP| de eventos, en kW",
    )
    timestamp_analisis: datetime = Field(
        examples=["2026-10-05T03:30:00Z"],
        description="Cuándo se ejecutó el análisis NILM (ISO 8601 UTC)",
    )
    fuente: str = Field(
        default="NILM-DBSCAN",
        examples=["NILM-DBSCAN"],
        description="Algoritmo que detectó esta máquina",
    )


class ListaMaquinasInferidaDTO(BaseModel):
    """Conjunto de máquinas inferidas para un dispositivo."""

    dispositivo_id: str = Field(
        min_length=1, examples=["planta_2_a"], description="ID del dispositivo"
    )
    maquinas_inferidas: list[MaquinaInferidaDTO] = Field(
        examples=[[]], description="Lista de máquinas detectadas por NILM"
    )
    actualizado_en: datetime = Field(
        examples=["2026-10-05T03:30:00Z"],
        description="Cuándo se actualizó este análisis (ISO 8601 UTC)",
    )
