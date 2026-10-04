"""src/infrastructure/fastapi/routers/clasificar.py — Endpoints de inferencia supervisada."""

from typing import Annotated

from fastapi import APIRouter, Depends

from src.application.cargas.dtos.clasificacion import (
    ClassifyBayesRequest,
    ClassifyBayesResponse,
    ClassifyKNNRequest,
    ClassifyKNNResponse,
)
from src.application.cargas.dtos.explicabilidad import ExplicarArbolResponse
from src.application.cargas.dtos.metricas import MetricasResponse
from src.application.cargas.use_cases.clasificar_bayes import ClasificarBayesUseCase
from src.application.cargas.use_cases.clasificar_knn import ClasificarKNNUseCase
from src.application.cargas.use_cases.explicar_arbol import ExplicarArbolUseCase
from src.application.cargas.use_cases.obtener_metricas import ObtenerMetricasUseCase
from src.infrastructure.fastapi.dependencies import (
    get_clasificar_bayes_use_case,
    get_clasificar_knn_use_case,
    get_explicar_arbol_use_case,
    get_obtener_metricas_use_case,
)

router = APIRouter(tags=["Clasificación"])


@router.post("/classify/bayes", response_model=ClassifyBayesResponse)
def classify_bayes(
    caso_de_uso: Annotated[ClasificarBayesUseCase, Depends(get_clasificar_bayes_use_case)],
    request: ClassifyBayesRequest,
) -> ClassifyBayesResponse:
    """Clasificación probabilística de contingencias en transformadores eléctricos con Naive Bayes."""
    return caso_de_uso.execute(request)


@router.post("/classify/knn", response_model=ClassifyKNNResponse)
def classify_knn(
    caso_de_uso: Annotated[ClasificarKNNUseCase, Depends(get_clasificar_knn_use_case)],
    request: ClassifyKNNRequest,
) -> ClassifyKNNResponse:
    """Clasificación de firmas eléctricas basada en instancias (k-NN) y normalización z-score."""
    return caso_de_uso.execute(request)


@router.get("/metrics", response_model=MetricasResponse)
def obtener_metricas(
    caso_de_uso: Annotated[ObtenerMetricasUseCase, Depends(get_obtener_metricas_use_case)],
) -> MetricasResponse:
    """Métricas de desempeño del modelo supervisado: matriz de confusión, F1, accuracy."""
    return caso_de_uso.execute()


@router.get("/explain/tree", response_model=ExplicarArbolResponse)
def explicar_arbol(
    caso_de_uso: Annotated[ExplicarArbolUseCase, Depends(get_explicar_arbol_use_case)],
) -> ExplicarArbolResponse:
    """Árbol de decisión CART serializado: estructura recursiva de nodos de decisión y hojas."""
    return caso_de_uso.execute()
