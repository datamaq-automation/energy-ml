"""Composición de dependencias del módulo SIBO."""

from __future__ import annotations

from fastapi import Request

from sibo.application.use_cases.consultar_registros import (
    ConsultarRegistrosUseCase,
    EliminarRegistroUseCase,
)
from sibo.application.use_cases.estimar_gases import EstimarGasesUseCase
from sibo.application.use_cases.listar_alimentos import ListarAlimentosUseCase
from sibo.application.use_cases.recomendar_alimentos import RecomendarAlimentosUseCase
from sibo.application.use_cases.registrar_comida import RegistrarComidaUseCase
from sibo.domain.ports import AlimentoRepository, PredictorGases, RegistroRepository


def get_alimentos(request: Request) -> AlimentoRepository:
    return request.app.state.alimentos


def get_registros(request: Request) -> RegistroRepository:
    return request.app.state.registros


def get_predictor(request: Request) -> PredictorGases:
    return request.app.state.predictor


def get_listar_alimentos(request: Request) -> ListarAlimentosUseCase:
    return ListarAlimentosUseCase(alimentos=get_alimentos(request))


def get_registrar_comida(request: Request) -> RegistrarComidaUseCase:
    return RegistrarComidaUseCase(
        alimentos=get_alimentos(request),
        registros=get_registros(request),
    )


def get_consultar_registros(request: Request) -> ConsultarRegistrosUseCase:
    return ConsultarRegistrosUseCase(
        alimentos=get_alimentos(request),
        registros=get_registros(request),
    )


def get_eliminar_registro(request: Request) -> EliminarRegistroUseCase:
    return EliminarRegistroUseCase(registros=get_registros(request))


def get_estimar_gases(request: Request) -> EstimarGasesUseCase:
    return EstimarGasesUseCase(
        alimentos=get_alimentos(request),
        registros=get_registros(request),
        predictor=get_predictor(request),
    )


def get_recomendar_alimentos(request: Request) -> RecomendarAlimentosUseCase:
    return RecomendarAlimentosUseCase(
        alimentos=get_alimentos(request),
        registros=get_registros(request),
    )
