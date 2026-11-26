"""src/application/residuos/use_cases/pronosticar_residuos.py — Serie, validación y pronóstico."""

from __future__ import annotations

from typing import Generic, TypeVar

from src.application.residuos.dtos.pronosticar_residuos_request import (
    PronosticarResiduosRequest,
)
from src.application.residuos.dtos.pronosticar_residuos_response import (
    PronosticarResiduosResponse,
)
from src.application.residuos.mappers.informe_residuos_mapper import InformeResiduosMapper
from src.domain.residuos.entities import InformeResiduos
from src.domain.residuos.repositories import PronosticadorResiduos, RepositorioResiduos

Datos = TypeVar("Datos")


class PronosticarResiduosUseCase(Generic[Datos]):
    """Arma la serie de la ciudad, valida los modelos en el último año y pronostica 3 meses."""

    def __init__(
        self,
        repositorio: RepositorioResiduos[Datos],
        pronosticador: PronosticadorResiduos[Datos],
    ) -> None:
        self._repositorio = repositorio
        self._pronosticador = pronosticador

    def execute(self, request: PronosticarResiduosRequest) -> PronosticarResiduosResponse:
        """Corre las tres etapas y, si se pide, guarda los resultados."""
        registros = self._repositorio.cargar()
        informe = InformeResiduos(id=request.id_informe)
        informe.registrar_serie(self._pronosticador.serie_mensual(registros))
        informe.registrar_validacion(self._pronosticador.validar(registros))
        informe.registrar_pronosticos(self._pronosticador.pronosticar(registros))
        archivos: list[str] = []
        if request.guardar_resultados:
            archivos = self._repositorio.guardar(
                informe.serie, informe.metricas, informe.pronosticos
            )
        return InformeResiduosMapper.a_response(informe, archivos)
