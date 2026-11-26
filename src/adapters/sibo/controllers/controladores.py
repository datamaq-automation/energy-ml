"""src/adapters/sibo/controllers/controladores.py — Orquestación HTTP sin FastAPI."""

from __future__ import annotations

from datetime import date, datetime

from src.adapters.sibo.controllers.esquemas import RegistroCreateRequest, Sintomas2HRequest
from src.adapters.sibo.presenters.respuestas import (
    AlimentoResponse,
    RecomendacionResponse,
    RegistroResponse,
    SaludResponse,
    SerieGasesResponse,
    Sintomas2HResponse,
)
from src.application.sibo.dtos.consultar_registros import ConsultarRegistrosRequest
from src.application.sibo.dtos.eliminar_registro import EliminarRegistroRequest
from src.application.sibo.dtos.estimar_gases import EstimarGasesRequest
from src.application.sibo.dtos.listar_alimentos import ListarAlimentosRequest
from src.application.sibo.dtos.recomendar_alimentos import RecomendarAlimentosRequest
from src.application.sibo.dtos.registrar_comida import RegistrarComidaRequest
from src.application.sibo.dtos.registrar_sintomas_2h import RegistrarSintomas2HRequest
from src.application.sibo.use_cases.consultar_registros import (
    ConsultarRegistrosUseCase,
    EliminarRegistroUseCase,
)
from src.application.sibo.use_cases.estimar_gases import EstimarGasesUseCase
from src.application.sibo.use_cases.listar_alimentos import ListarAlimentosUseCase
from src.application.sibo.use_cases.recomendar_alimentos import RecomendarAlimentosUseCase
from src.application.sibo.use_cases.registrar_comida import RegistrarComidaUseCase
from src.application.sibo.use_cases.registrar_sintomas_2h import RegistrarSintomas2HUseCase

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


def registrar_sintomas_2h(
    caso: RegistrarSintomas2HUseCase,
    registro_id: int,
    request: Sintomas2HRequest,
) -> Sintomas2HResponse:
    peticion = RegistrarSintomas2HRequest(
        registro_id=registro_id,
        sintomas=request.sintomas,
        fecha=request.fecha,
    )
    return Sintomas2HResponse(**caso.execute(peticion).model_dump())


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
