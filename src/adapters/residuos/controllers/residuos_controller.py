"""src/adapters/residuos/controllers/residuos_controller.py — Entrada → caso de uso."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.adapters.residuos.presenters.residuos_presenter import ResiduosPresenter
from src.application.residuos.dtos.pronosticar_residuos_request import (
    PronosticarResiduosRequest,
)
from src.application.residuos.dtos.pronosticar_residuos_response import (
    PronosticarResiduosResponse,
)
from src.application.residuos.use_cases.pronosticar_residuos import PronosticarResiduosUseCase


class ResiduosController:
    """Arma el request desde valores primitivos, ejecuta el caso de uso y presenta el resultado."""

    def __init__(
        self, caso_de_uso: PronosticarResiduosUseCase[Any], presentador: ResiduosPresenter
    ) -> None:
        self._caso_de_uso = caso_de_uso
        self._presentador = presentador

    def pronosticar(
        self, guardar_resultados: bool, ahora: datetime
    ) -> tuple[PronosticarResiduosResponse, list[str]]:
        """Identifica la corrida por fecha y hora; devuelve la respuesta y sus líneas de reporte."""
        request = PronosticarResiduosRequest(
            id_informe=f"residuos-{ahora:%Y%m%dT%H%M%S}",
            guardar_resultados=guardar_resultados,
        )
        respuesta = self._caso_de_uso.execute(request)
        return respuesta, self._presentador.presentar(respuesta)
