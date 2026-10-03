"""src/infrastructure/fastapi/dependencies.py — Composición de dependencias para los routers."""

from pathlib import Path

from src.application.cargas.use_cases.identificar_cargas import IdentificarCargasUseCase
from src.domain.cargas.repositories import MedicionRepository
from src.infrastructure.csv.medicion_repository import CsvMedicionRepository
from src.infrastructure.settings.config import get_settings
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.dbscan_agrupador import DbscanAgrupador


def get_mediciones() -> MedicionRepository:
    return CsvMedicionRepository(Path(get_settings().MEDICIONES_CSV_DIR))


def get_identificar_cargas() -> IdentificarCargasUseCase:
    settings = get_settings()
    return IdentificarCargasUseCase(
        mediciones=get_mediciones(),
        agrupador=DbscanAgrupador(min_eventos=settings.NILM_MIN_EVENTOS),
        umbral_kw=settings.NILM_UMBRAL_KW,
        logger=logger,
        balance_minimo=settings.NILM_BALANCE_MINIMO,
        separacion_minima=settings.NILM_SEPARACION_MINIMA,
        radio_kw=settings.NILM_EPS_KW,
    )
