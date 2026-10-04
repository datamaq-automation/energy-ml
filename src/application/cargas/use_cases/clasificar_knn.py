"""src/application/cargas/use_cases/clasificar_knn.py — Caso de uso para clasificación de firmas eléctricas con k-NN."""

from src.application.cargas.dtos.clasificacion import (
    ClassifyKNNRequest,
    ClassifyKNNResponse,
    VecinoDTO,
)
from src.domain.cargas.entities import FirmaElectrica
from src.domain.cargas.repositories import ClasificadorKNN


class ClasificarKNNUseCase:
    """Ejecuta la clasificación basada en instancias (k-NN) para firmas eléctricas."""

    def __init__(self, clasificador: ClasificadorKNN) -> None:
        self._clasificador = clasificador

    def execute(self, request: ClassifyKNNRequest) -> ClassifyKNNResponse:
        firma = FirmaElectrica(
            potencia_activa_kw=request.potencia_activa_kw,
            potencia_reactiva_kvar=request.potencia_reactiva_kvar,
            thd_corriente=request.thd_corriente,
            factor_desbalance=request.factor_desbalance,
        )
        diagnostico = self._clasificador.clasificar_firma(
            firma,
            k=request.k,
            metrica=request.metrica,
        )
        vecinos_dto = [
            VecinoDTO(clase=v.clase, distancia=round(v.distancia, 4)) for v in diagnostico.vecinos
        ]
        return ClassifyKNNResponse(
            clase_predicha=diagnostico.clase_predicha,
            confianza=round(diagnostico.confianza, 4),
            distancia_promedio=round(diagnostico.distancia_promedio, 4),
            vecinos=vecinos_dto,
        )
