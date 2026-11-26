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
from src.application.sibo.dtos import RegistrarComidaCommand
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
    return [AlimentoResponse.desde(alimento) for alimento in caso.execute(busqueda)]


def registrar_comida(
    caso: RegistrarComidaUseCase,
    request: RegistroCreateRequest,
) -> RegistroResponse:
    command = RegistrarComidaCommand(
        alimento_id=request.alimento_id,
        porcion_g=request.porcion_g,
        fecha_hora=request.fecha_hora,
        sintomas=request.sintomas,
        notas=request.notas,
    )
    return RegistroResponse.desde(caso.execute(command))


def listar_registros(
    caso: ConsultarRegistrosUseCase,
    desde: datetime | None,
    hasta: datetime | None,
) -> list[RegistroResponse]:
    return [RegistroResponse.desde(detalle) for detalle in caso.execute(desde, hasta)]


def eliminar_registro(caso: EliminarRegistroUseCase, registro_id: int) -> None:
    caso.execute(registro_id)


def estimar_gases(
    caso: EstimarGasesUseCase,
    rango: str,
    fecha: date | None,
) -> SerieGasesResponse:
    return SerieGasesResponse.desde_serie(caso.execute(rango, fecha))


def recomendar_alimentos(
    caso: RecomendarAlimentosUseCase,
    limite: int,
) -> list[RecomendacionResponse]:
    return [RecomendacionResponse.desde(item) for item in caso.execute(limite)]


def salud() -> SaludResponse:
    return SaludResponse(status="ok", modulo="sibo", version=VERSION)
