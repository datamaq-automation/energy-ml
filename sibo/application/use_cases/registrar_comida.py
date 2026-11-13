"""Caso de uso: registrar una comida consumida por el usuario."""

from __future__ import annotations

from datetime import datetime

from sibo.application.dtos import RegistroCreateRequest, RegistroResponse
from sibo.domain.entities import RegistroComida
from sibo.domain.ports import AlimentoRepository, RegistroRepository


class RegistrarComidaUseCase:
    def __init__(
        self,
        alimentos: AlimentoRepository,
        registros: RegistroRepository,
    ) -> None:
        self._alimentos = alimentos
        self._registros = registros

    def execute(self, request: RegistroCreateRequest) -> RegistroResponse:
        alimento = self._alimentos.obtener(request.alimento_id)
        if alimento is None:
            raise LookupError(f"No existe el alimento {request.alimento_id}")

        registro = RegistroComida(
            fecha_hora=request.fecha_hora or datetime.now(),
            alimento_id=request.alimento_id,
            porcion_g=request.porcion_g,
            sintomas=request.sintomas,
            notas=request.notas.strip(),
        )
        creado = self._registros.crear(registro)
        return RegistroResponse.desde(creado, alimento)
