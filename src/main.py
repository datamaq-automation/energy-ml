"""src/main.py — Entrypoint principal de la aplicación FastAPI."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.infrastructure.fastapi.lifespan import lifespan
from src.infrastructure.fastapi.routers.cargas import router as cargas_router
from src.infrastructure.fastapi.routers.clasificar import router as clasificar_router
from src.infrastructure.fastapi.routers.mediciones import router as mediciones_router
from src.infrastructure.settings.config import get_settings
from src.infrastructure.settings.logger import logger


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(cargas_router, prefix=settings.API_V1_PREFIX)
    app.include_router(clasificar_router, prefix=settings.API_V1_PREFIX)
    app.include_router(mediciones_router, prefix=settings.API_V1_PREFIX)

    @app.exception_handler(LookupError)
    async def medidor_desconocido(request: Request, exc: LookupError) -> JSONResponse:
        logger.warning("Respondiendo 404: %s", exc)
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    app.mount("/static", StaticFiles(directory="web"), name="static")

    @app.get("/", include_in_schema=False)
    async def energia() -> FileResponse:
        return FileResponse("web/energia.html")

    @app.get("/guia", include_in_schema=False)
    async def guia() -> FileResponse:
        return FileResponse("web/guia.html")

    # Solo se publica el cuaderno del alumno: la guía docente tiene las respuestas.
    @app.get("/guia/cuaderno-alumno.md", include_in_schema=False)
    async def guia_markdown() -> FileResponse:
        return FileResponse("docs/cuaderno-alumno.md", media_type="text/markdown; charset=utf-8")

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "environment": settings.ENVIRONMENT}

    logger.info("Aplicación FastAPI creada")
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
