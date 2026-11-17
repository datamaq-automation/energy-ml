"""src/application/sibo/use_cases/listar_alimentos.py — Caso de uso para consultar alimentos."""

from __future__ import annotations

from src.domain.sibo.entities import Alimento
from src.domain.sibo.ports import AlimentoRepository


class ListarAlimentosUseCase:
    """Devuelve la base nutricional filtrada por nombre o categoría."""

    def __init__(self, alimentos: AlimentoRepository) -> None:
        self._alimentos = alimentos

    def execute(self, busqueda: str | None = None) -> list[Alimento]:
        termino = busqueda.strip() if busqueda else None
        return self._alimentos.listar(termino)
