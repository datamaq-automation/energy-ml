"""src/infrastructure/mediciones_factory.py — Factoría de repositorios de mediciones.

Patrón: una sola instancia del repositorio SSH por proceso.
"""

from functools import lru_cache
from pathlib import Path

from src.domain.cargas.repositories import MedicionRepository
from src.infrastructure.csv.medicion_repository import CsvMedicionRepository
from src.infrastructure.settings.config import Settings
from src.infrastructure.settings.logger import logger
from src.infrastructure.ssh.medicion_repository import SshMedicionRepository


@lru_cache(maxsize=1)
def crear_repositorio_mediciones(source: str, csv_dir: str, cache_dir: str) -> MedicionRepository:
    """Factoría única por proceso. Parámetros hashables para caché.

    Args:
        source: "local" o "ssh"
        csv_dir: ruta a data/input
        cache_dir: ruta a data/prod-cache

    Returns:
        CsvMedicionRepository o SshMedicionRepository (instancia única por proceso)
    """
    if source == "ssh":
        logger.info("🏭 Factoría: creando repositorio SSH (cache: %s)", cache_dir)
        return SshMedicionRepository(cache_dir=Path(cache_dir))
    else:
        logger.info("🏭 Factoría: creando repositorio CSV local (%s)", csv_dir)
        return CsvMedicionRepository(Path(csv_dir))


def get_mediciones(settings: Settings) -> MedicionRepository:
    """Obtener repositorio según configuración."""
    return crear_repositorio_mediciones(
        source=settings.MEDICIONES_SOURCE,
        csv_dir=settings.MEDICIONES_CSV_DIR,
        cache_dir=settings.MEDICIONES_CACHE_DIR,
    )
