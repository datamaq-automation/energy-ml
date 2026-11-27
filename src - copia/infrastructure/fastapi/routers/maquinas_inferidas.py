"""src/infrastructure/fastapi/routers/maquinas_inferidas.py — Endpoint para máquinas inferidas por NILM."""

from fastapi import APIRouter, Depends, HTTPException

from src.application.cargas.dtos.maquinas_inferidas import (
    ListaMaquinasInferidaDTO,
)
from src.application.cargas.use_cases.consultar_maquinas_inferidas import (
    ConsultarMaquinasInferidaUseCase,
)
from src.infrastructure.fastapi.dependencies import (
    obtener_use_case_consultar_maquinas,
)

router = APIRouter(tags=["maquinas"])


@router.get(
    "/dispositivos/{dispositivo_id}/maquinas/inferidas",
    response_model=ListaMaquinasInferidaDTO,
    summary="Máquinas inferidas por NILM",
    description="Retorna máquinas/cargas detectadas por análisis NILM para un dispositivo.",
    responses={
        404: {"description": "Dispositivo sin análisis NILM o no encontrado"},
        503: {"description": "Cache de datos vacío o desactualizado"},
    },
)
async def obtener_maquinas_inferidas(
    dispositivo_id: str,
    use_case: ConsultarMaquinasInferidaUseCase = Depends(obtener_use_case_consultar_maquinas),
) -> ListaMaquinasInferidaDTO:
    """Obtiene máquinas inferidas por NILM para un dispositivo.

    Args:
        dispositivo_id: ID del dispositivo (ej: "planta_2_a")

    Returns:
        ListaMaquinasInferidaDTO con máquinas detectadas, confianza y métricas

    Raises:
        404: Si no hay análisis NILM para el dispositivo
        503: Si el cache está vacío
    """
    try:
        return use_case.ejecutar(dispositivo_id)
    except RuntimeError as e:
        # Sin análisis NILM
        if "Sin análisis NILM" in str(e):
            raise HTTPException(
                status_code=404,
                detail=f"Dispositivo '{dispositivo_id}' sin análisis NILM o no encontrado",
            ) from e
        # Error genérico de cache/runtime
        raise HTTPException(
            status_code=503,
            detail="Cache de datos vacío o desactualizado",
        ) from e
