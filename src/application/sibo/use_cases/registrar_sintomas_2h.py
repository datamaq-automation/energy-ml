"""src/application/sibo/use_cases/registrar_sintomas_2h.py — Caso de uso de la etiqueta real."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from src.application.sibo.dtos.registrar_sintomas_2h import (
    RegistrarSintomas2HRequest,
    RegistrarSintomas2HResponse,
)
from src.application.sibo.mappers.sibo_mapper import SiboMapper
from src.domain.sibo.events import Sintomas2HRegistrados
from src.domain.sibo.exceptions import RegistroNoEncontradoError
from src.domain.sibo.repositories import RegistroRepository
from src.domain.sibo.services import es_seguimiento_valido


class RegistrarSintomas2HUseCase:
    """Guarda el malestar informado a las 2 h, única etiqueta usada para entrenar."""

    def __init__(self, registros: RegistroRepository) -> None:
        self._registros = registros

    def execute(self, request: RegistrarSintomas2HRequest) -> RegistrarSintomas2HResponse:
        registro = self._registros.obtener(request.registro_id)
        if registro is None:
            raise RegistroNoEncontradoError(request.registro_id)

        fecha = request.fecha or datetime.now()
        candidato = replace(registro, sintomas_2h=request.sintomas)
        if not es_seguimiento_valido(candidato, fecha):
            raise ValueError("El seguimiento debe medirse entre 1,5 y 4 h después de la comida")

        actualizado = self._registros.registrar_sintomas_2h(
            request.registro_id, request.sintomas, fecha
        )
        if actualizado is None:
            raise RegistroNoEncontradoError(request.registro_id)

        evento = Sintomas2HRegistrados(
            registro_id=actualizado.id or request.registro_id,
            sintomas=request.sintomas,
            fecha=fecha,
        )
        return SiboMapper.sintomas_a_response(evento)
