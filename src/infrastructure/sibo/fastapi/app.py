"""src/infrastructure/sibo/fastapi/app.py — Aplicación FastAPI del módulo SIBO."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.adapters.sibo.controllers.controladores import salud
from src.adapters.sibo.presenters.respuestas import SaludResponse
from src.domain.sibo.value_objects import PoliticaModelo
from src.infrastructure.sibo.database import BaseDatos
from src.infrastructure.sibo.fastapi.routers.alimentos import router as alimentos_router
from src.infrastructure.sibo.fastapi.routers.gases import router as gases_router
from src.infrastructure.sibo.fastapi.routers.recomendaciones import router as recomendaciones_router
from src.infrastructure.sibo.fastapi.routers.registros import router as registros_router
from src.infrastructure.sibo.ml.modelo_hibrido import ModeloGasesHibrido
from src.infrastructure.sibo.seed import sembrar_si_vacio

RAIZ = Path(__file__).resolve().parents[1]
DIRECTORIO_WEB = RAIZ / "web"
RUTA_SEMILLA = RAIZ / "data" / "alimentos.csv"
RUTA_DB = RAIZ / "data" / "sibo.db"
PREFIJO_API = "/api/sibo"


def create_app(ruta_db: str | Path | None = None) -> FastAPI:
    base_datos = BaseDatos(ruta_db or RUTA_DB)
    base_datos.inicializar()
    sembrar_si_vacio(base_datos, RUTA_SEMILLA)

    app = FastAPI(
        title="SIBO ML API",
        version="1.0.0",
        description=(
            "Herramienta de apoyo para el seguimiento nutricional de personas con SIBO. "
            "No sustituye diagnóstico ni tratamiento médico."
        ),
    )
    app.state.base_datos = base_datos
    app.state.predictor = ModeloGasesHibrido(politica=PoliticaModelo())

    for router in (
        alimentos_router,
        gases_router,
        recomendaciones_router,
        registros_router,
    ):
        app.include_router(router, prefix=PREFIJO_API)

    @app.get(f"{PREFIJO_API}/salud", response_model=SaludResponse, tags=["Salud"])
    def estado() -> SaludResponse:
        return salud()

    app.mount("/static", StaticFiles(directory=str(DIRECTORIO_WEB)), name="static")

    @app.get("/", include_in_schema=False)
    async def inicio() -> FileResponse:
        return FileResponse(DIRECTORIO_WEB / "index.html")

    @app.exception_handler(LookupError)
    async def no_encontrado(request: Request, exc: LookupError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def solicitud_invalida(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    return app
