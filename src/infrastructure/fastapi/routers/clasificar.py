"""src/infrastructure/fastapi/routers/clasificar.py — Endpoints de inferencia supervisada."""

from typing import Annotated

from fastapi import APIRouter, Depends

from src.application.cargas.dtos.clasificacion import (
    ClassifyBayesRequest,
    ClassifyBayesResponse,
    ClassifyKNNRequest,
    ClassifyKNNResponse,
)
from src.application.cargas.use_cases.clasificar_bayes import ClasificarBayesUseCase
from src.application.cargas.use_cases.clasificar_knn import ClasificarKNNUseCase
from src.infrastructure.fastapi.dependencies import (
    get_clasificar_bayes_use_case,
    get_clasificar_knn_use_case,
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
