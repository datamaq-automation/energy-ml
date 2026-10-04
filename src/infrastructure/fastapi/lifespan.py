"""src/infrastructure/fastapi/lifespan.py — Gestor de ciclo de vida de la aplicación y carga de modelos."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from src.infrastructure.settings.config import describir_nilm, get_settings
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.bayes_clasificador import BayesClasificador
from src.infrastructure.sklearn.knn_clasificador import KNNClasificador


def cargar_modelos(modelos_dir: Path | str) -> dict[str, Any]:
    """Carga los modelos serializados o entrena versiones base por defecto."""
    dir_path = Path(modelos_dir)
    dir_path.mkdir(parents=True, exist_ok=True)

    ruta_bayes = dir_path / "bayes.joblib"
    ruta_knn = dir_path / "knn.joblib"

    bayes = BayesClasificador.cargar_o_entrenar(ruta_bayes)
    knn = KNNClasificador.cargar_o_entrenar(ruta_knn)

    return {
        "bayes": bayes,
        "knn": knn,
    }


def recargar_modelos(app: FastAPI) -> None:
    """Soporte de recarga en caliente (hot-reload) para artefactos serializados."""
    settings = get_settings()
    logger.info("Recargando modelos en caliente desde %s", settings.MODELOS_DIR)
    app.state.modelos = cargar_modelos(settings.MODELOS_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Ciclo de vida de FastAPI: inicialización y liberación de recursos compartidos."""
    settings = get_settings()
    logger.info(describir_nilm(settings))
    logger.info("Inicializando modelos de machine learning en app.state.modelos...")

    app.state.modelos = cargar_modelos(settings.MODELOS_DIR)
    logger.info(
        "Modelos cargados exitosamente: %s",
        list(app.state.modelos.keys()),
    )

    # Sincronizar con VPS si está en modo prod (fail-fast)
    if settings.MEDICIONES_SOURCE == "ssh":
        logger.info("🔄 Modo PROD: sincronizando mediciones desde VPS...")
        from src.infrastructure.mediciones_factory import get_mediciones

        try:
            repo = get_mediciones(settings)
            if hasattr(repo, "sincronizar"):
                repo.sincronizar()
            logger.info("✅ Mediciones del VPS sincronizadas al startup")
        except RuntimeError as e:
            logger.error("❌ Fallo al sincronizar con VPS: %s", e)
            raise

    yield

    logger.info("Liberando memoria de modelos de app.state.modelos...")
    if hasattr(app.state, "modelos") and isinstance(app.state.modelos, dict):
        app.state.modelos.clear()
    logger.info("Aplicación detenida")
