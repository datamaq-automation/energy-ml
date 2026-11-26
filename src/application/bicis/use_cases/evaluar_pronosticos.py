"""src/application/bicis/use_cases/evaluar_pronosticos.py — Orquesta la evaluación temporal."""

from __future__ import annotations

from src.application.bicis.dtos.evaluar_pronosticos_request import EvaluarPronosticosRequest
from src.application.bicis.dtos.evaluar_pronosticos_response import EvaluarPronosticosResponse
from src.application.bicis.dtos.preparar_pronosticos_request import PrepararPronosticosRequest
from src.application.bicis.mappers.informe_pronosticos_mapper import InformePronosticosMapper
from src.application.bicis.use_cases.preparar_pronosticos import PrepararPronosticosUseCase
from src.domain.bicis.entities import InformePronosticos
from src.domain.bicis.events import PronosticosEvaluados
from src.domain.bicis.repositories import ModeladorPronosticos
from src.domain.bicis.services import validar_periodo


class EvaluarPronosticosUseCase:
    """Prepara datos sin fuga, delega el modelo y construye el informe final."""

    def __init__(
        self, preparador: PrepararPronosticosUseCase, modelador: ModeladorPronosticos
    ) -> None:
        self._preparador = preparador
        self._modelador = modelador

    def execute(self, request: EvaluarPronosticosRequest) -> EvaluarPronosticosResponse:
        """Evalúa la línea base y el modelo sobre el período solicitado."""
        validar_periodo(request.desde, request.hasta)
        preparacion = self._preparador.execute(
            PrepararPronosticosRequest(desde=request.desde, hasta=request.hasta)
        )
        evaluacion = self._modelador.evaluar(preparacion.muestras)
        informe = InformePronosticos(
            id=request.id_informe,
            evaluacion=evaluacion,
            dias_faltantes=preparacion.dias_faltantes,
            dias_sin_rezagos=preparacion.dias_sin_rezagos,
            eventos=(
                PronosticosEvaluados(
                    informe_id=request.id_informe,
                    desde=request.desde,
                    hasta=request.hasta,
                    dias_prueba=evaluacion.dias_prueba,
                ),
            ),
        )
        return InformePronosticosMapper.a_response(informe)
