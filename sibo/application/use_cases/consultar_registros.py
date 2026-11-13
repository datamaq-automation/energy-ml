"""Casos de uso: consultar y eliminar registros de comidas."""

from __future__ import annotations

from datetime import datetime

from sibo.application.dtos import RegistroResponse
from sibo.domain.ports import AlimentoRepository, RegistroRepository


class ConsultarRegistrosUseCase:
    def __init__(
        self,
        alimentos: AlimentoRepository,
        registros: RegistroRepository,
    ) -> None:
        self._alimentos = alimentos
        self._registros = registros

    def execute(
        self,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[RegistroResponse]:
        registros = self._registros.listar(desde, hasta)
        alimentos = {
            a.id: a for a in self._alimentos.listar_por_ids({r.alimento_id for r in registros})
        }
        return [
            RegistroResponse.desde(registro, alimentos[registro.alimento_id])
            for registro in registros
            if registro.alimento_id in alimentos
        ]


class EliminarRegistroUseCase:
    def __init__(self, registros: RegistroRepository) -> None:
        self._registros = registros

    def execute(self, registro_id: int) -> None:
        if not self._registros.eliminar(registro_id):
            raise LookupError(f"No existe el registro {registro_id}")
