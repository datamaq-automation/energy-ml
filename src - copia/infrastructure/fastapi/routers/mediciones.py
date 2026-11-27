"""src/infrastructure/fastapi/routers/mediciones.py — Endpoints sobre fuente de mediciones."""

from fastapi import APIRouter, Depends

from src.application.cargas.dtos.mediciones_fuente import (
    MedicionesFuenteResponse,
    UltimaDescargaResponse,
)
from src.domain.cargas.repositories import MedicionRepository
from src.infrastructure.fastapi.dependencies import get_mediciones
from src.infrastructure.settings.config import get_settings
from src.infrastructure.settings.logger import logger
from src.infrastructure.ssh.medicion_repository import SshMedicionRepository

router = APIRouter(tags=["Mediciones"])


@router.get("/mediciones/fuente", response_model=MedicionesFuenteResponse)
def obtener_fuente_mediciones(
    repo: MedicionRepository = Depends(get_mediciones),
) -> MedicionesFuenteResponse:
    """Retorna información sobre la fuente actual de mediciones.

    - **dev**: datos locales en data/input/
    - **prod**: datos descargados desde VPS via SSH

    Response:
        - `fuente`: "local" o "ssh"
        - `medidores`: lista de medidores disponibles
        - `ultima_descarga`: metadatos (solo en SSH)
    """
    settings = get_settings()
    medidores = repo.medidores()

    # En modo SSH, incluir metadatos de descarga
    ultima_descarga = None
    if isinstance(repo, SshMedicionRepository):
        info = repo.ultima_descarga_info()
        ultima_descarga = UltimaDescargaResponse(
            instante=info["instante"],
            duracion_segundos=info["duracion_segundos"],
            filas_por_medidor=info["filas_por_medidor"],
        )
        logger.info(
            "📊 Fuente SSH: %d medidores, descarga en %.1f seg",
            len(medidores),
            info["duracion_segundos"],
        )
    else:
        logger.info("📂 Fuente local: %d medidores disponibles", len(medidores))

    return MedicionesFuenteResponse(
        fuente=settings.MEDICIONES_SOURCE,
        medidores=medidores,
        ultima_descarga=ultima_descarga,
    )
