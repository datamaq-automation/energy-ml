"""src/application/logistica/use_cases/analizar_retrasos.py — Tareas A, B y C de logística."""

from __future__ import annotations

from typing import Generic, TypeVar

from src.application.logistica.dtos.analizar_retrasos_request import AnalizarRetrasosRequest
from src.application.logistica.dtos.analizar_retrasos_response import AnalizarRetrasosResponse
from src.application.logistica.mappers.informe_retrasos_mapper import InformeRetrasosMapper
from src.domain.logistica.entities import InformeRetrasos
from src.domain.logistica.repositories import ModeladorRetrasos, RepositorioPedidos

Datos = TypeVar("Datos")


class AnalizarRetrasosUseCase(Generic[Datos]):
    """Orquesta A (agrupar y perfilar), B (clasificar) y C (recall por segmento)."""

    def __init__(
        self, repositorio: RepositorioPedidos[Datos], modelador: ModeladorRetrasos[Datos]
    ) -> None:
        self._repositorio = repositorio
        self._modelador = modelador

    def execute(self, request: AnalizarRetrasosRequest) -> AnalizarRetrasosResponse:
        """Corre las tres tareas, guarda los gráficos y devuelve el informe."""
        pedidos = self._repositorio.cargar()
        informe = InformeRetrasos(
            id=request.id_informe, pedidos=self._modelador.contar_filas(pedidos)
        )

        metricas_k, perfiles = self._modelador.agrupar(pedidos, best_k=request.best_k)
        informe.registrar_agrupamiento(metricas_k, perfiles)
        destino = request.destino_graficos
        graficos = [
            self._modelador.graficar_codo(metricas_k, request.best_k, destino),
        ]

        modelos, importancias, segmentos = self._modelador.clasificar(
            pedidos, max_depth=request.max_depth, segmento=request.segmento
        )
        informe.registrar_clasificacion(modelos, importancias, segmentos)
        graficos.append(self._modelador.graficar_matriz(informe.modelo_final, destino))
        return InformeRetrasosMapper.a_response(informe, graficos)
