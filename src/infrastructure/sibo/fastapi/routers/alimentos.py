"""src/infrastructure/sibo/fastapi/routers/alimentos.py — Endpoints de alimentos."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.adapters.sibo.controllers.controladores import listar_alimentos as listar_alimentos_http
from src.adapters.sibo.presenters.respuestas import AlimentoResponse
from src.application.sibo.use_cases.listar_alimentos import ListarAlimentosUseCase
from src.infrastructure.sibo.fastapi.dependencies import get_listar_alimentos

router = APIRouter(prefix="/alimentos", tags=["Alimentos"])


@router.get("", response_model=list[AlimentoResponse])
def listar_alimentos(
    caso_de_uso: Annotated[ListarAlimentosUseCase, Depends(get_listar_alimentos)],
    busqueda: Annotated[str | None, Query(max_length=80)] = None,
) -> list[AlimentoResponse]:
    return listar_alimentos_http(caso_de_uso, busqueda)
