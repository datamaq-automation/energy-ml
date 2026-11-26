"""src/application/sibo/use_cases/listar_alimentos.py — Caso de uso para consultar alimentos."""

from __future__ import annotations

from src.application.sibo.dtos.listar_alimentos import (
    ListarAlimentosRequest,
    ListarAlimentosResponse,
)
from src.application.sibo.mappers.sibo_mapper import SiboMapper
from src.domain.sibo.repositories import AlimentoRepository


class ListarAlimentosUseCase:
    """Devuelve la base nutricional filtrada por nombre o categoría."""

    def __init__(self, alimentos: AlimentoRepository) -> None:
        self._alimentos = alimentos

    def execute(self, request: ListarAlimentosRequest) -> ListarAlimentosResponse:
        termino = request.busqueda.strip() if request.busqueda else None
        return ListarAlimentosResponse(
            alimentos=[SiboMapper.alimento_a_dto(a) for a in self._alimentos.listar(termino)]
        )
