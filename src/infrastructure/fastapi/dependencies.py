"""src/infrastructure/fastapi/dependencies.py — Composición de dependencias para los routers."""

from functools import lru_cache

from sqlalchemy import Engine, create_engine

from src.application.cargas.use_cases.identificar_cargas import IdentificarCargasUseCase
from src.infrastructure.settings.config import get_settings
from src.infrastructure.sklearn.dbscan_agrupador import DbscanAgrupador
from src.infrastructure.sqlalchemy.medicion_repository import SqlMedicionRepository


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().DATABASE_URL, pool_pre_ping=True)


def get_identificar_cargas() -> IdentificarCargasUseCase:
    settings = get_settings()
    return IdentificarCargasUseCase(
        mediciones=SqlMedicionRepository(get_engine()),
        agrupador=DbscanAgrupador(eps_kw=settings.NILM_EPS_KW, min_eventos=settings.NILM_MIN_EVENTOS),
        umbral_kw=settings.NILM_UMBRAL_KW,
    )
