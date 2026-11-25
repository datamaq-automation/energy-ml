"""src/adapters/medioambiente/controllers/episodios_co_controller.py — Entrada → caso de uso."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.adapters.medioambiente.presenters.episodios_co_presenter import EpisodiosCOPresenter
from src.application.medioambiente.dtos.analizar_episodios_request import (
    AnalizarEpisodiosRequest,
)
from src.application.medioambiente.dtos.analizar_episodios_response import (
    AnalizarEpisodiosResponse,
)
from src.application.medioambiente.use_cases.analizar_episodios_co import (
    AnalizarEpisodiosCOUseCase,
)


class EpisodiosCOController:
    """Arma el request desde valores primitivos, ejecuta el caso de uso y presenta el resultado."""

    def __init__(
        self,
        caso_de_uso: AnalizarEpisodiosCOUseCase[Any],
        presentador: EpisodiosCOPresenter,
    ) -> None:
        self._caso_de_uso = caso_de_uso
        self._presentador = presentador

    def analizar(
        self, destino_graficos: str, ahora: datetime
    ) -> tuple[AnalizarEpisodiosResponse, list[str]]:
        """Identifica la corrida por fecha y hora; devuelve la respuesta y sus líneas de reporte."""
        request = AnalizarEpisodiosRequest(
            id_informe=f"episodios-co-{ahora:%Y%m%dT%H%M%S}",
            destino_graficos=destino_graficos,
        )
        respuesta = self._caso_de_uso.execute(request)
        return respuesta, self._presentador.presentar(respuesta)
