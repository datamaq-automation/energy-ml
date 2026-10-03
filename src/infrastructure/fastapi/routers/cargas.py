"""src/infrastructure/fastapi/routers/cargas.py — Endpoints de identificación de cargas (thin controller)."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError

from src.application.cargas.dtos.identificar_cargas import IdentificarCargasRequest, IdentificarCargasResponse
from src.application.cargas.use_cases.identificar_cargas import IdentificarCargasUseCase
from src.infrastructure.fastapi.dependencies import get_identificar_cargas

router = APIRouter(tags=["Cargas"])


@router.get("/identify-loads", response_model=IdentificarCargasResponse)
def identificar_cargas(
    caso_de_uso: Annotated[IdentificarCargasUseCase, Depends(get_identificar_cargas)],
    medidor: Annotated[str, Query(examples=["Trafo arriba"])],
    desde: datetime,
    hasta: datetime,
) -> IdentificarCargasResponse:
    try:
        request = IdentificarCargasRequest(medidor=medidor, desde=desde, hasta=hasta)
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=error.errors(include_url=False, include_context=False, include_input=False)) from error
    return caso_de_uso.execute(request)
