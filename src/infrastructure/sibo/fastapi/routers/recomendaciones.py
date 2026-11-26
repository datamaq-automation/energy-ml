"""src/infrastructure/sibo/fastapi/routers/recomendaciones.py — Endpoints de recomendaciones."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.adapters.sibo.controllers.controladores import (
    recomendar_alimentos as recomendar_alimentos_http,
)
from src.adapters.sibo.presenters.respuestas import RecomendacionResponse
from src.application.sibo.use_cases.recomendar_alimentos import RecomendarAlimentosUseCase
from src.infrastructure.sibo.fastapi.dependencies import get_recomendar_alimentos

router = APIRouter(prefix="/recomendaciones", tags=["Recomendaciones"])


@router.get("", response_model=list[RecomendacionResponse])
def recomendar_alimentos(
    caso_de_uso: Annotated[RecomendarAlimentosUseCase, Depends(get_recomendar_alimentos)],
    limite: Annotated[int, Query(ge=1, le=20)] = 6,
) -> list[RecomendacionResponse]:
    return recomendar_alimentos_http(caso_de_uso, limite)
