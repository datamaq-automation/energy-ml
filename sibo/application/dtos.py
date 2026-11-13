"""DTOs de entrada y salida del módulo SIBO (Pydantic v2)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from sibo.domain.entities import Alimento, PuntoGases, Recomendacion, RegistroComida


class AlimentoResponse(BaseModel):
    id: int
    nombre: str
    categoria: str
    porcion_base_g: float
    kcal: float
    proteinas_g: float
    carbohidratos_g: float
    grasas_g: float
    fibra_g: float
    fodmap: str
    score_inflamatorio: float
    score_desinflamatorio: float
    notas: str

    @classmethod
    def desde(cls, alimento: Alimento) -> AlimentoResponse:
        return cls(
            id=alimento.id,
            nombre=alimento.nombre,
            categoria=alimento.categoria,
            porcion_base_g=alimento.porcion_base_g,
            kcal=alimento.kcal,
            proteinas_g=alimento.proteinas_g,
            carbohidratos_g=alimento.carbohidratos_g,
            grasas_g=alimento.grasas_g,
            fibra_g=alimento.fibra_g,
            fodmap=alimento.fodmap,
            score_inflamatorio=alimento.score_inflamatorio,
            score_desinflamatorio=alimento.score_desinflamatorio,
            notas=alimento.notas,
        )


class RegistroCreateRequest(BaseModel):
    alimento_id: int = Field(gt=0)
    porcion_g: float = Field(gt=0, le=5000)
    fecha_hora: datetime | None = None
    sintomas: float = Field(default=0.0, ge=0, le=10)
    notas: str = Field(default="", max_length=500)


class RegistroResponse(BaseModel):
    id: int
    fecha_hora: datetime
    alimento_id: int
    alimento_nombre: str
    categoria: str
    fodmap: str
    porcion_g: float
    sintomas: float
    notas: str
    score_inflamatorio: float
    score_desinflamatorio: float

    @classmethod
    def desde(cls, registro: RegistroComida, alimento: Alimento) -> RegistroResponse:
        return cls(
            id=registro.id or 0,
            fecha_hora=registro.fecha_hora,
            alimento_id=registro.alimento_id,
            alimento_nombre=alimento.nombre,
            categoria=alimento.categoria,
            fodmap=alimento.fodmap,
            porcion_g=registro.porcion_g,
            sintomas=registro.sintomas,
            notas=registro.notas,
            score_inflamatorio=alimento.score_inflamatorio,
            score_desinflamatorio=alimento.score_desinflamatorio,
        )


class PuntoGasesResponse(BaseModel):
    instante: datetime
    nivel_estimado: float
    nivel_bajo: float
    nivel_alto: float

    @classmethod
    def desde(cls, punto: PuntoGases) -> PuntoGasesResponse:
        return cls(
            instante=punto.instante,
            nivel_estimado=punto.nivel_estimado,
            nivel_bajo=punto.nivel_bajo,
            nivel_alto=punto.nivel_alto,
        )


class SerieGasesResponse(BaseModel):
    rango: str
    desde: datetime
    hasta: datetime
    unidad: str = "nivel relativo 0-100"
    promedio: float
    pico: float
    puntos: list[PuntoGasesResponse]


class RecomendacionResponse(BaseModel):
    alimento: AlimentoResponse
    puntaje: float
    motivo: str

    @classmethod
    def desde(cls, recomendacion: Recomendacion) -> RecomendacionResponse:
        return cls(
            alimento=AlimentoResponse.desde(recomendacion.alimento),
            puntaje=recomendacion.puntaje,
            motivo=recomendacion.motivo,
        )


class SaludResponse(BaseModel):
    status: str
    modulo: str
    version: str
