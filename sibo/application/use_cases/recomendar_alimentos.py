"""Caso de uso: recomendar alimentos desinflamatorios según el historial."""

from __future__ import annotations

from datetime import datetime, timedelta

from sibo.application.dtos import RecomendacionResponse
from sibo.domain.entities import Alimento, Recomendacion
from sibo.domain.ports import AlimentoRepository, RegistroRepository
from sibo.domain.servicios import factor_fodmap, motivo_recomendacion


class RecomendarAlimentosUseCase:
    def __init__(
        self,
        alimentos: AlimentoRepository,
        registros: RegistroRepository,
    ) -> None:
        self._alimentos = alimentos
        self._registros = registros

    def execute(
        self,
        limite: int = 6,
        ahora: datetime | None = None,
    ) -> list[RecomendacionResponse]:
        momento = ahora or datetime.now()
        recientes = self._registros.listar(momento - timedelta(days=7), momento)
        consumidos = {registro.alimento_id for registro in recientes}

        recomendaciones = [
            self._evaluar(alimento, alimento.id in consumidos)
            for alimento in self._alimentos.listar()
        ]
        recomendaciones.sort(key=lambda r: r.puntaje, reverse=True)
        return [
            RecomendacionResponse.desde(recomendacion) for recomendacion in recomendaciones[:limite]
        ]

    def _evaluar(self, alimento: Alimento, consumido: bool) -> Recomendacion:
        puntaje = (
            alimento.score_desinflamatorio * 10.0
            - alimento.score_inflamatorio * 7.0
            - factor_fodmap(alimento.fodmap) * 20.0
            + min(alimento.fibra_g, 5.0) * 1.5
        )
        if alimento.fodmap == "alto":
            puntaje -= 15.0
        if consumido:
            puntaje -= 4.0
        return Recomendacion(
            alimento=alimento,
            puntaje=round(puntaje, 1),
            motivo=motivo_recomendacion(alimento, consumido),
        )
