"""src/infrastructure/sqlalchemy/medicion_repository.py — Lectura de potencia desde datamaq_telemetry."""

from datetime import datetime

from sqlalchemy import DateTime, Engine, Float, text

from src.domain.cargas.entities import Medicion
from src.infrastructure.settings.logger import logger

W_POR_KW = 1000.0

_CONSULTA = text(
    """
    SELECT t.recorded_at, t.total_active_power
    FROM telemetry_instantaneous t
    JOIN devices d ON d.id = t.device_id
    WHERE d.name = :medidor
      AND t.recorded_at >= :desde AND t.recorded_at < :hasta
      AND t.total_active_power IS NOT NULL
      AND t.es_dato_confiable = 1
    ORDER BY t.recorded_at
    """
).columns(recorded_at=DateTime, total_active_power=Float)


class SqlMedicionRepository:
    """Implementa MedicionRepository; convierte W (como guarda el medidor) a kW."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def listar(self, medidor: str, desde: datetime, hasta: datetime) -> list[Medicion]:
        logger.info("Consultando MySQL: %s", medidor)
        with self._engine.connect() as conexion:
            filas = conexion.execute(_CONSULTA, {"medidor": medidor, "desde": desde, "hasta": hasta})
            mediciones = [Medicion(instante=f[0], potencia_kw=float(f[1]) / W_POR_KW) for f in filas]
        logger.info("%d mediciones recibidas de MySQL", len(mediciones))
        return mediciones
