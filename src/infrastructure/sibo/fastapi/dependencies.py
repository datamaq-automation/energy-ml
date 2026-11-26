"""src/infrastructure/sibo/fastapi/dependencies.py — Composición de dependencias SIBO."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request

from src.adapters.sibo.gateways.alimento_repository import SqliteAlimentoRepository
from src.adapters.sibo.gateways.registro_repository import SqliteRegistroRepository
from src.application.sibo.use_cases.consultar_registros import (
    ConsultarRegistrosUseCase,
    EliminarRegistroUseCase,
)
from src.application.sibo.use_cases.estimar_gases import EstimarGasesUseCase
from src.application.sibo.use_cases.listar_alimentos import ListarAlimentosUseCase
from src.application.sibo.use_cases.recomendar_alimentos import RecomendarAlimentosUseCase
from src.application.sibo.use_cases.registrar_comida import RegistrarComidaUseCase
from src.domain.sibo.ports import AlimentoRepository, PredictorGases, RegistroRepository
from src.infrastructure.sibo.database import BaseDatos


def get_base_datos(request: Request) -> BaseDatos:
    return request.app.state.base_datos


def get_conexion(
    base_datos: Annotated[BaseDatos, Depends(get_base_datos)],
) -> Iterator[sqlite3.Connection]:
    with base_datos.conexion() as conexion:
        yield conexion


def get_alimentos(
    conexion: Annotated[sqlite3.Connection, Depends(get_conexion)],
) -> AlimentoRepository:
    return SqliteAlimentoRepository(conexion)


def get_registros(
    conexion: Annotated[sqlite3.Connection, Depends(get_conexion)],
) -> RegistroRepository:
    return SqliteRegistroRepository(conexion)


def get_predictor(request: Request) -> PredictorGases:
    return request.app.state.predictor


def get_listar_alimentos(
    alimentos: Annotated[AlimentoRepository, Depends(get_alimentos)],
) -> ListarAlimentosUseCase:
    return ListarAlimentosUseCase(alimentos=alimentos)


def get_registrar_comida(
    alimentos: Annotated[AlimentoRepository, Depends(get_alimentos)],
    registros: Annotated[RegistroRepository, Depends(get_registros)],
) -> RegistrarComidaUseCase:
    return RegistrarComidaUseCase(alimentos=alimentos, registros=registros)


def get_consultar_registros(
    alimentos: Annotated[AlimentoRepository, Depends(get_alimentos)],
    registros: Annotated[RegistroRepository, Depends(get_registros)],
) -> ConsultarRegistrosUseCase:
    return ConsultarRegistrosUseCase(alimentos=alimentos, registros=registros)


def get_eliminar_registro(
    registros: Annotated[RegistroRepository, Depends(get_registros)],
) -> EliminarRegistroUseCase:
    return EliminarRegistroUseCase(registros=registros)


def get_estimar_gases(
    alimentos: Annotated[AlimentoRepository, Depends(get_alimentos)],
    registros: Annotated[RegistroRepository, Depends(get_registros)],
    predictor: Annotated[PredictorGases, Depends(get_predictor)],
) -> EstimarGasesUseCase:
    return EstimarGasesUseCase(
        alimentos=alimentos,
        registros=registros,
        predictor=predictor,
    )


def get_recomendar_alimentos(
    alimentos: Annotated[AlimentoRepository, Depends(get_alimentos)],
    registros: Annotated[RegistroRepository, Depends(get_registros)],
) -> RecomendarAlimentosUseCase:
    return RecomendarAlimentosUseCase(alimentos=alimentos, registros=registros)
