"""src/infrastructure/sibo/fastapi/routers/registros.py — Endpoints de registros."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from src.adapters.sibo.controllers.controladores import (
    eliminar_registro as eliminar_registro_http,
)
from src.adapters.sibo.controllers.controladores import (
    listar_registros as listar_registros_http,
)
from src.adapters.sibo.controllers.controladores import (
    registrar_comida as registrar_comida_http,
)
from src.adapters.sibo.controllers.controladores import (
    registrar_sintomas_2h as registrar_sintomas_2h_http,
)
from src.adapters.sibo.controllers.esquemas import RegistroCreateRequest, Sintomas2HRequest
from src.adapters.sibo.presenters.respuestas import RegistroResponse, Sintomas2HResponse
from src.application.sibo.use_cases.consultar_registros import (
    ConsultarRegistrosUseCase,
    EliminarRegistroUseCase,
)
from src.application.sibo.use_cases.registrar_comida import RegistrarComidaUseCase
from src.application.sibo.use_cases.registrar_sintomas_2h import RegistrarSintomas2HUseCase
from src.infrastructure.sibo.fastapi.dependencies import (
    get_consultar_registros,
    get_eliminar_registro,
    get_registrar_comida,
    get_registrar_sintomas_2h,
)

router = APIRouter(prefix="/registros", tags=["Registros"])


@router.post("", response_model=RegistroResponse, status_code=status.HTTP_201_CREATED)
def registrar_comida(
    request: RegistroCreateRequest,
    caso_de_uso: Annotated[RegistrarComidaUseCase, Depends(get_registrar_comida)],
) -> RegistroResponse:
    return registrar_comida_http(caso_de_uso, request)


@router.get("", response_model=list[RegistroResponse])
def listar_registros(
    caso_de_uso: Annotated[ConsultarRegistrosUseCase, Depends(get_consultar_registros)],
    desde: Annotated[datetime | None, Query()] = None,
    hasta: Annotated[datetime | None, Query()] = None,
) -> list[RegistroResponse]:
    return listar_registros_http(caso_de_uso, desde, hasta)


@router.patch("/{registro_id}/sintomas-2h", response_model=Sintomas2HResponse)
def registrar_sintomas_2h(
    registro_id: int,
    request: Sintomas2HRequest,
    caso_de_uso: Annotated[RegistrarSintomas2HUseCase, Depends(get_registrar_sintomas_2h)],
) -> Sintomas2HResponse:
    return registrar_sintomas_2h_http(caso_de_uso, registro_id, request)


@router.delete("/{registro_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_registro(
    registro_id: int,
    caso_de_uso: Annotated[EliminarRegistroUseCase, Depends(get_eliminar_registro)],
) -> Response:
    eliminar_registro_http(caso_de_uso, registro_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
