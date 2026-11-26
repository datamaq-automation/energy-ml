"""src/adapters/bicis/controllers/pronosticos_controller.py — Entrada → caso de uso."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from src.adapters.bicis.presenters.pronosticos_presenter import PronosticosPresenter
from src.application.bicis.dtos.evaluar_pronosticos_request import EvaluarPronosticosRequest
from src.application.bicis.dtos.evaluar_pronosticos_response import EvaluarPronosticosResponse
from src.application.bicis.use_cases.evaluar_pronosticos import EvaluarPronosticosUseCase


class PronosticosController:
    """Crea el request, ejecuta el caso de uso y devuelve líneas para consola."""

    def __init__(
        self, caso_de_uso: EvaluarPronosticosUseCase, presentador: PronosticosPresenter
    ) -> None:
        self._caso_de_uso = caso_de_uso
        self._presentador = presentador

    def evaluar(self, desde: date, hasta: date) -> tuple[EvaluarPronosticosResponse, list[str]]:
        """Evalúa el intervalo usando un identificador distinto para cada corrida."""
        request = EvaluarPronosticosRequest(
            id_informe=f"bicis-{uuid4().hex}",
            desde=desde,
            hasta=hasta,
        )
        respuesta = self._caso_de_uso.execute(request)
        return respuesta, self._presentador.presentar(respuesta)
