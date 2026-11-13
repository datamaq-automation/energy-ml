"""Entrypoint del módulo SIBO: uvicorn sibo.main:app --port 8001."""

from __future__ import annotations

from sibo.infrastructure.fastapi.app import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("sibo.main:app", host="0.0.0.0", port=8001, reload=True)
