"""src/infrastructure/fastapi/dependencies.py — Composición de dependencias para los routers."""

from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine

from src.application.cargas.use_cases.identificar_cargas import IdentificarCargasUseCase
from src.domain.cargas.repositories import MedicionRepository
from src.infrastructure.csv.medicion_repository import CsvMedicionRepository
from src.infrastructure.settings.config import get_settings
from src.infrastructure.sklearn.dbscan_agrupador import DbscanAgrupador
from src.infrastructure.sqlalchemy.medicion_repository import SqlMedicionRepository


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().DATABASE_URL, pool_pre_ping=True)


def get_mediciones() -> MedicionRepository:
    settings = get_settings()
    if settings.MEDICIONES_FUENTE == "mysql":
        return SqlMedicionRepository(get_engine())
    return CsvMedicionRepository(Path(settings.MEDICIONES_CSV_DIR))


def get_identificar_cargas() -> IdentificarCargasUseCase:
    settings = get_settings()
    return IdentificarCargasUseCase(
        mediciones=get_mediciones(),
        agrupador=DbscanAgrupador(eps_kw=settings.NILM_EPS_KW, min_eventos=settings.NILM_MIN_EVENTOS),
        umbral_kw=settings.NILM_UMBRAL_KW,
    )
