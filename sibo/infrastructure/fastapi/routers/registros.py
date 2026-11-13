"""Endpoints de registro diario de comidas."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from sibo.application.dtos import RegistroCreateRequest, RegistroResponse
from sibo.application.use_cases.consultar_registros import (
    ConsultarRegistrosUseCase,
    EliminarRegistroUseCase,
)
from sibo.application.use_cases.registrar_comida import RegistrarComidaUseCase
from sibo.infrastructure.fastapi.dependencies import (
    get_consultar_registros,
    get_eliminar_registro,
    get_registrar_comida,
)

router = APIRouter(prefix="/registros", tags=["Registros"])


@router.post("", response_model=RegistroResponse, status_code=status.HTTP_201_CREATED)
def registrar_comida(
    request: RegistroCreateRequest,
    caso_de_uso: Annotated[RegistrarComidaUseCase, Depends(get_registrar_comida)],
) -> RegistroResponse:
    return caso_de_uso.execute(request)


@router.get("", response_model=list[RegistroResponse])
def listar_registros(
    caso_de_uso: Annotated[ConsultarRegistrosUseCase, Depends(get_consultar_registros)],
    desde: Annotated[datetime | None, Query()] = None,
    hasta: Annotated[datetime | None, Query()] = None,
) -> list[RegistroResponse]:
    return caso_de_uso.execute(desde, hasta)


@router.delete("/{registro_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_registro(
    registro_id: int,
    caso_de_uso: Annotated[EliminarRegistroUseCase, Depends(get_eliminar_registro)],
) -> Response:
    caso_de_uso.execute(registro_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
