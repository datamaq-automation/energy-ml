"""Caso de uso: listar y buscar alimentos de la base nutricional."""

from __future__ import annotations

from sibo.application.dtos import AlimentoResponse
from sibo.domain.ports import AlimentoRepository


class ListarAlimentosUseCase:
    def __init__(self, alimentos: AlimentoRepository) -> None:
        self._alimentos = alimentos

    def execute(self, busqueda: str | None = None) -> list[AlimentoResponse]:
        return [AlimentoResponse.desde(a) for a in self._alimentos.listar(busqueda)]
