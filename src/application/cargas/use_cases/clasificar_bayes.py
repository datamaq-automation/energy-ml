"""src/application/cargas/use_cases/clasificar_bayes.py — Caso de uso para clasificación bayesiana de contingencias."""

from src.application.cargas.dtos.clasificacion import ClassifyBayesRequest, ClassifyBayesResponse
from src.domain.cargas.entities import TelemetriaTransformador
from src.domain.cargas.repositories import ClasificadorBayes


class ClasificarBayesUseCase:
    """Ejecuta el análisis probabilístico Naive Bayes para diagnóstico de transformadores."""

    def __init__(self, clasificador: ClasificadorBayes) -> None:
        self._clasificador = clasificador

    def execute(self, request: ClassifyBayesRequest) -> ClassifyBayesResponse:
        telemetria = TelemetriaTransformador(
            potencia_kva=request.potencia_kva,
            temperatura_aceite_c=request.temperatura_aceite_c,
            temperatura_devanados_c=request.temperatura_devanados_c,
            corriente_a=request.corriente_a,
        )
        diagnostico = self._clasificador.predecir_contingencia(telemetria)
        return ClassifyBayesResponse(
            estado=diagnostico.estado,
            probabilidades=diagnostico.probabilidades,
            es_contingencia=diagnostico.es_contingencia,
            mensaje=diagnostico.mensaje,
        )
