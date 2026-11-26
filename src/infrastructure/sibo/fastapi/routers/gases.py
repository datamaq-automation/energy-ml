"""src/infrastructure/sibo/fastapi/routers/gases.py — Endpoints de la curva de gases."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.adapters.sibo.controllers.controladores import estimar_gases as estimar_gases_http
from src.adapters.sibo.presenters.respuestas import SerieGasesResponse
from src.application.sibo.use_cases.estimar_gases import EstimarGasesUseCase
from src.infrastructure.sibo.fastapi.dependencies import get_estimar_gases

router = APIRouter(prefix="/gases", tags=["Gases"])


@router.get("", response_model=SerieGasesResponse)
def estimar_gases(
    caso_de_uso: Annotated[EstimarGasesUseCase, Depends(get_estimar_gases)],
    rango: Annotated[str, Query(pattern="^(dia|semana|mes)$")] = "dia",
    fecha: Annotated[date | None, Query()] = None,
) -> SerieGasesResponse:
    return estimar_gases_http(caso_de_uso, rango, fecha)
