"""src/adapters/sibo/controllers/controladores.py — Orquestación HTTP sin FastAPI."""

from __future__ import annotations

from datetime import date, datetime

from src.adapters.sibo.controllers.esquemas import RegistroCreateRequest
from src.adapters.sibo.presenters.respuestas import (
    AlimentoResponse,
    RecomendacionResponse,
    RegistroResponse,
    SaludResponse,
    SerieGasesResponse,
)
from src.application.sibo.dtos.consultar_registros import ConsultarRegistrosRequest
from src.application.sibo.dtos.eliminar_registro import EliminarRegistroRequest
from src.application.sibo.dtos.estimar_gases import EstimarGasesRequest
from src.application.sibo.dtos.listar_alimentos import ListarAlimentosRequest
from src.application.sibo.dtos.recomendar_alimentos import RecomendarAlimentosRequest
from src.application.sibo.dtos.registrar_comida import RegistrarComidaRequest
from src.application.sibo.use_cases.consultar_registros import (
    ConsultarRegistrosUseCase,
    EliminarRegistroUseCase,
)
from src.application.sibo.use_cases.estimar_gases import EstimarGasesUseCase
from src.application.sibo.use_cases.listar_alimentos import ListarAlimentosUseCase
from src.application.sibo.use_cases.recomendar_alimentos import RecomendarAlimentosUseCase
from src.application.sibo.use_cases.registrar_comida import RegistrarComidaUseCase

VERSION = "1.0.0"


def listar_alimentos(
    caso: ListarAlimentosUseCase,
    busqueda: str | None,
) -> list[AlimentoResponse]:
    respuesta = caso.execute(ListarAlimentosRequest(busqueda=busqueda))
    return [AlimentoResponse(**alimento.model_dump()) for alimento in respuesta.alimentos]


def registrar_comida(
    caso: RegistrarComidaUseCase,
    request: RegistroCreateRequest,
) -> RegistroResponse:
    peticion = RegistrarComidaRequest(**request.model_dump())
    return RegistroResponse(**caso.execute(peticion).model_dump())


def listar_registros(
    caso: ConsultarRegistrosUseCase,
    desde: datetime | None,
    hasta: datetime | None,
) -> list[RegistroResponse]:
    respuesta = caso.execute(ConsultarRegistrosRequest(desde=desde, hasta=hasta))
    return [RegistroResponse(**registro.model_dump()) for registro in respuesta.registros]


def eliminar_registro(caso: EliminarRegistroUseCase, registro_id: int) -> None:
    caso.execute(EliminarRegistroRequest(registro_id=registro_id))


def estimar_gases(
    caso: EstimarGasesUseCase,
    rango: str,
    fecha: date | None,
) -> SerieGasesResponse:
    respuesta = caso.execute(EstimarGasesRequest(rango=rango, fecha=fecha))
    return SerieGasesResponse(**respuesta.model_dump())


def recomendar_alimentos(
    caso: RecomendarAlimentosUseCase,
    limite: int,
) -> list[RecomendacionResponse]:
    respuesta = caso.execute(RecomendarAlimentosRequest(limite=limite))
    return [RecomendacionResponse(**item.model_dump()) for item in respuesta.recomendaciones]


def salud() -> SaludResponse:
    return SaludResponse(status="ok", modulo="sibo", version=VERSION)
