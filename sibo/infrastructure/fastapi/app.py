"""Aplicación FastAPI autocontenida del módulo SIBO."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from sibo.infrastructure.fastapi.routers import (
    alimentos,
    gases,
    recomendaciones,
    registros,
    salud,
)
from sibo.infrastructure.ml.modelo_hibrido import ModeloGasesHibrido
from sibo.infrastructure.sqlite.alimento_repository import SqliteAlimentoRepository
from sibo.infrastructure.sqlite.database import BaseDatos
from sibo.infrastructure.sqlite.registro_repository import SqliteRegistroRepository
from sibo.infrastructure.sqlite.seed import sembrar_si_vacio

RAIZ = Path(__file__).resolve().parents[2]
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
    app.state.alimentos = SqliteAlimentoRepository(base_datos)
    app.state.registros = SqliteRegistroRepository(base_datos)
    app.state.predictor = ModeloGasesHibrido()

    for router in (
        alimentos.router,
        gases.router,
        recomendaciones.router,
        registros.router,
        salud.router,
    ):
        app.include_router(router, prefix=PREFIJO_API)

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
