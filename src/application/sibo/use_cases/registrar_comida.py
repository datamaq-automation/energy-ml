"""src/application/sibo/use_cases/registrar_comida.py — Caso de uso para registrar comidas."""

from __future__ import annotations

from datetime import datetime

from src.application.sibo.dtos.registrar_comida import (
    RegistrarComidaRequest,
    RegistrarComidaResponse,
)
from src.application.sibo.mappers.sibo_mapper import SiboMapper
from src.domain.sibo.entities import RegistroComida
from src.domain.sibo.events import ComidaRegistrada
from src.domain.sibo.exceptions import AlimentoNoEncontradoError
from src.domain.sibo.repositories import AlimentoRepository, RegistroRepository


class RegistrarComidaUseCase:
    """Valida el alimento y persiste una comida con su contexto."""

    def __init__(
        self,
        alimentos: AlimentoRepository,
        registros: RegistroRepository,
    ) -> None:
        self._alimentos = alimentos
        self._registros = registros

    def execute(self, request: RegistrarComidaRequest) -> RegistrarComidaResponse:
        """Guarda la comida y devuelve la respuesta con el evento de dominio emitido."""
        alimento = self._alimentos.obtener(request.alimento_id)
        if alimento is None:
            raise AlimentoNoEncontradoError(request.alimento_id)

        registro = RegistroComida(
            fecha_hora=request.fecha_hora or datetime.now(),
            alimento_id=request.alimento_id,
            porcion_g=request.porcion_g,
            sintomas=request.sintomas,
            notas=request.notas.strip(),
        )
        creado = self._registros.crear(registro)
        evento = ComidaRegistrada(
            registro_id=creado.id or 0,
            alimento_id=creado.alimento_id,
            fecha_hora=creado.fecha_hora,
            porcion_g=creado.porcion_g,
        )
        return SiboMapper.registro_a_response(creado, alimento, evento)
