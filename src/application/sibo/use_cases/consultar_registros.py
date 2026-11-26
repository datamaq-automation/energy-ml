"""src/application/sibo/use_cases/consultar_registros.py — Casos de uso de registros."""

from __future__ import annotations

from src.application.sibo.dtos.consultar_registros import (
    ConsultarRegistrosRequest,
    ConsultarRegistrosResponse,
)
from src.application.sibo.dtos.eliminar_registro import (
    EliminarRegistroRequest,
    EliminarRegistroResponse,
)
from src.application.sibo.mappers.sibo_mapper import SiboMapper
from src.domain.sibo.events import RegistroEliminado
from src.domain.sibo.exceptions import RegistroNoEncontradoError
from src.domain.sibo.repositories import AlimentoRepository, RegistroRepository


class ConsultarRegistrosUseCase:
    """Lista registros enriquecidos con los datos del alimento consumido."""

    def __init__(
        self,
        alimentos: AlimentoRepository,
        registros: RegistroRepository,
    ) -> None:
        self._alimentos = alimentos
        self._registros = registros

    def execute(self, request: ConsultarRegistrosRequest) -> ConsultarRegistrosResponse:
        """Devuelve el historial dentro de la ventana pedida."""
        registros = self._registros.listar(request.desde, request.hasta)
        alimentos = {
            a.id: a for a in self._alimentos.listar_por_ids({r.alimento_id for r in registros})
        }
        return ConsultarRegistrosResponse(
            registros=[
                SiboMapper.registro_a_response(registro, alimentos[registro.alimento_id])
                for registro in registros
                if registro.alimento_id in alimentos
            ]
        )


class EliminarRegistroUseCase:
    """Elimina un registro o falla si no existe."""

    def __init__(self, registros: RegistroRepository) -> None:
        self._registros = registros

    def execute(self, request: EliminarRegistroRequest) -> EliminarRegistroResponse:
        """Confirma la baja con el identificador del evento de dominio."""
        if not self._registros.eliminar(request.registro_id):
            raise RegistroNoEncontradoError(request.registro_id)
        evento = RegistroEliminado(registro_id=request.registro_id)
        return SiboMapper.registro_eliminado_a_response(evento)
