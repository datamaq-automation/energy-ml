"""src/adapters/presenters/sibo/respuestas.py — Esquemas HTTP y mapeo desde el dominio."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from src.application.sibo.dtos import RegistroDetallado, SerieGases
from src.domain.sibo.entities import Alimento, PuntoGases, Recomendacion


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
    def desde(cls, detalle: RegistroDetallado) -> RegistroResponse:
        registro = detalle.registro
        alimento = detalle.alimento
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

    @classmethod
    def desde_serie(cls, serie: SerieGases) -> SerieGasesResponse:
        return cls(
            rango=serie.rango,
            desde=serie.desde,
            hasta=serie.hasta,
            promedio=serie.promedio,
            pico=serie.pico,
            puntos=[PuntoGasesResponse.desde(punto) for punto in serie.puntos],
        )


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
