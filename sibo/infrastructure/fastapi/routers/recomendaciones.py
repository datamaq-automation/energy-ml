"""Endpoints de recomendación de alimentos desinflamatorios."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from sibo.application.dtos import RecomendacionResponse
from sibo.application.use_cases.recomendar_alimentos import RecomendarAlimentosUseCase
from sibo.infrastructure.fastapi.dependencies import get_recomendar_alimentos

router = APIRouter(prefix="/recomendaciones", tags=["Recomendaciones"])


@router.get("", response_model=list[RecomendacionResponse])
def recomendar_alimentos(
    caso_de_uso: Annotated[RecomendarAlimentosUseCase, Depends(get_recomendar_alimentos)],
    limite: Annotated[int, Query(ge=1, le=20)] = 6,
) -> list[RecomendacionResponse]:
    return caso_de_uso.execute(limite)
