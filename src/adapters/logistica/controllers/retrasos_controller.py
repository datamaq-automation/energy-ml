"""src/adapters/logistica/controllers/retrasos_controller.py — Entrada → caso de uso."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.adapters.logistica.presenters.retrasos_presenter import RetrasosPresenter
from src.application.logistica.dtos.analizar_retrasos_request import AnalizarRetrasosRequest
from src.application.logistica.dtos.analizar_retrasos_response import AnalizarRetrasosResponse
from src.application.logistica.use_cases.analizar_retrasos import AnalizarRetrasosUseCase


class RetrasosController:
    """Arma el request desde valores primitivos, ejecuta el caso de uso y presenta el resultado."""

    def __init__(
        self, caso_de_uso: AnalizarRetrasosUseCase[Any], presentador: RetrasosPresenter
    ) -> None:
        self._caso_de_uso = caso_de_uso
        self._presentador = presentador

    def analizar(
        self, best_k: int, max_depth: int, destino_graficos: str, ahora: datetime
    ) -> tuple[AnalizarRetrasosResponse, list[str]]:
        """Identifica la corrida por fecha y hora; devuelve la respuesta y sus líneas de reporte."""
        request = AnalizarRetrasosRequest(
            id_informe=f"retrasos-{ahora:%Y%m%dT%H%M%S}",
            best_k=best_k,
            max_depth=max_depth,
            destino_graficos=destino_graficos,
        )
        respuesta = self._caso_de_uso.execute(request)
        return respuesta, self._presentador.presentar(respuesta)
