"""Endpoints de la base nutricional."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from sibo.application.dtos import AlimentoResponse
from sibo.application.use_cases.listar_alimentos import ListarAlimentosUseCase
from sibo.infrastructure.fastapi.dependencies import get_listar_alimentos

router = APIRouter(prefix="/alimentos", tags=["Alimentos"])


@router.get("", response_model=list[AlimentoResponse])
def listar_alimentos(
    caso_de_uso: Annotated[ListarAlimentosUseCase, Depends(get_listar_alimentos)],
    busqueda: Annotated[str | None, Query(max_length=80)] = None,
) -> list[AlimentoResponse]:
    return caso_de_uso.execute(busqueda)
