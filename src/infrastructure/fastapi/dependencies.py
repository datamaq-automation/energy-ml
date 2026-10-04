"""src/infrastructure/fastapi/dependencies.py — Composición de dependencias para los routers."""

from pathlib import Path

from fastapi import Request

from src.application.cargas.use_cases.actualizar_version_space import ActualizarVersionSpaceUseCase
from src.application.cargas.use_cases.clasificar_bayes import ClasificarBayesUseCase
from src.application.cargas.use_cases.clasificar_knn import ClasificarKNNUseCase
from src.application.cargas.use_cases.explicar_arbol import ExplicarArbolUseCase
from src.application.cargas.use_cases.identificar_cargas import IdentificarCargasUseCase
from src.application.cargas.use_cases.inducir_reglas import (
    InducirReglasUseCase,
    ObtenerReglaUseCase,
)
from src.application.cargas.use_cases.obtener_metricas import (
    MatrizConfusionRepository,
    ObtenerMetricasUseCase,
)
from src.domain.cargas.repositories import (
    ClasificadorBayes,
    ClasificadorKNN,
    MedicionRepository,
)
from src.infrastructure.mediciones_factory import get_mediciones as factory_get_mediciones
from src.infrastructure.settings.config import get_settings
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.arbol_clasificador import ArbolClasificador
from src.infrastructure.sklearn.bayes_clasificador import BayesClasificador
from src.infrastructure.sklearn.dbscan_agrupador import DbscanAgrupador
from src.infrastructure.sklearn.knn_clasificador import KNNClasificador


def get_mediciones() -> MedicionRepository:
    settings = get_settings()
    return factory_get_mediciones(settings)


def get_identificar_cargas() -> IdentificarCargasUseCase:
    settings = get_settings()
    return IdentificarCargasUseCase(
        mediciones=get_mediciones(),
        agrupador=DbscanAgrupador(),
        umbral_kw=settings.NILM_UMBRAL_KW,
        logger=logger,
        balance_minimo=settings.NILM_BALANCE_MINIMO,
        separacion_minima=settings.NILM_SEPARACION_MINIMA,
        radio_kw=settings.NILM_EPS_KW,
        min_eventos=settings.NILM_MIN_EVENTOS,
    )


def get_clasificador_bayes(request: Request) -> ClasificadorBayes:
    if hasattr(request.app.state, "modelos") and "bayes" in request.app.state.modelos:
        return request.app.state.modelos["bayes"]
    settings = get_settings()
    return BayesClasificador.cargar_o_entrenar(Path(settings.MODELOS_DIR) / "bayes.joblib")


def get_clasificador_knn(request: Request) -> ClasificadorKNN:
    if hasattr(request.app.state, "modelos") and "knn" in request.app.state.modelos:
        return request.app.state.modelos["knn"]
    settings = get_settings()
    return KNNClasificador.cargar_o_entrenar(Path(settings.MODELOS_DIR) / "knn.joblib")


def get_clasificar_bayes_use_case(request: Request) -> ClasificarBayesUseCase:
    return ClasificarBayesUseCase(clasificador=get_clasificador_bayes(request))


def get_clasificar_knn_use_case(request: Request) -> ClasificarKNNUseCase:
    return ClasificarKNNUseCase(clasificador=get_clasificador_knn(request))


def get_obtener_metricas_use_case(request: Request) -> ObtenerMetricasUseCase:
    if hasattr(request.app.state, "matriz_confusion_repo"):
        repo = request.app.state.matriz_confusion_repo
    else:
        repo = MatrizConfusionRepository()
        request.app.state.matriz_confusion_repo = repo
    return ObtenerMetricasUseCase(matriz_confusion_repo=repo)


def get_explicar_arbol_use_case(request: Request) -> ExplicarArbolUseCase:
    if hasattr(request.app.state, "arbol_clasificador"):
        clasificador = request.app.state.arbol_clasificador
    else:
        clasificador = ArbolClasificador()
    return ExplicarArbolUseCase(clasificador=clasificador)


def get_actualizar_version_space_use_case(request: Request) -> ActualizarVersionSpaceUseCase:
    return ActualizarVersionSpaceUseCase()


def get_inducir_reglas_use_case(request: Request) -> InducirReglasUseCase:
    if hasattr(request.app.state, "arbol_clasificador"):
        clasificador = request.app.state.arbol_clasificador
    else:
        clasificador = ArbolClasificador()
    return InducirReglasUseCase(clasificador=clasificador)


def get_obtener_regla_use_case(request: Request) -> ObtenerReglaUseCase:
    if hasattr(request.app.state, "arbol_clasificador"):
        clasificador = request.app.state.arbol_clasificador
    else:
        clasificador = ArbolClasificador()
    return ObtenerReglaUseCase(clasificador=clasificador)
