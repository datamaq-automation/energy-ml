"""Endpoints de estimación de la curva de gases."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from sibo.application.dtos import SerieGasesResponse
from sibo.application.use_cases.estimar_gases import EstimarGasesUseCase
from sibo.infrastructure.fastapi.dependencies import get_estimar_gases

router = APIRouter(prefix="/gases", tags=["Gases"])


@router.get("", response_model=SerieGasesResponse)
def estimar_gases(
    caso_de_uso: Annotated[EstimarGasesUseCase, Depends(get_estimar_gases)],
    rango: Annotated[str, Query(pattern="^(dia|semana|mes)$")] = "dia",
    fecha: Annotated[date | None, Query()] = None,
) -> SerieGasesResponse:
    return caso_de_uso.execute(rango, fecha)
