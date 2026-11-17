"""src/application/sibo/use_cases/consultar_registros.py — Casos de uso de registros."""

from __future__ import annotations

from datetime import datetime

from src.application.sibo.dtos import RegistroDetallado
from src.domain.sibo.ports import AlimentoRepository, RegistroRepository


class ConsultarRegistrosUseCase:
    """Lista registros enriquecidos con los datos del alimento consumido."""

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
    ) -> list[RegistroDetallado]:
        registros = self._registros.listar(desde, hasta)
        alimentos = {
            a.id: a for a in self._alimentos.listar_por_ids({r.alimento_id for r in registros})
        }
        return [
            RegistroDetallado(registro=registro, alimento=alimentos[registro.alimento_id])
            for registro in registros
            if registro.alimento_id in alimentos
        ]


class EliminarRegistroUseCase:
    """Elimina un registro o falla si no existe."""

    def __init__(self, registros: RegistroRepository) -> None:
        self._registros = registros

    def execute(self, registro_id: int) -> None:
        if not self._registros.eliminar(registro_id):
            raise LookupError(f"No existe el registro {registro_id}")
