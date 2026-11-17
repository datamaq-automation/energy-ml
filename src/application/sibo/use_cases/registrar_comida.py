"""src/application/sibo/use_cases/registrar_comida.py — Caso de uso para registrar comidas."""

from __future__ import annotations

from datetime import datetime

from src.application.sibo.dtos import RegistrarComidaCommand, RegistroDetallado
from src.domain.sibo.entities import RegistroComida
from src.domain.sibo.ports import AlimentoRepository, RegistroRepository


class RegistrarComidaUseCase:
    """Valida el alimento y persiste una comida con su contexto."""

    def __init__(
        self,
        alimentos: AlimentoRepository,
        registros: RegistroRepository,
    ) -> None:
        self._alimentos = alimentos
        self._registros = registros

    def execute(self, command: RegistrarComidaCommand) -> RegistroDetallado:
        alimento = self._alimentos.obtener(command.alimento_id)
        if alimento is None:
            raise LookupError(f"No existe el alimento {command.alimento_id}")

        registro = RegistroComida(
            fecha_hora=command.fecha_hora or datetime.now(),
            alimento_id=command.alimento_id,
            porcion_g=command.porcion_g,
            sintomas=command.sintomas,
            notas=command.notas.strip(),
        )
        creado = self._registros.crear(registro)
        return RegistroDetallado(registro=creado, alimento=alimento)
