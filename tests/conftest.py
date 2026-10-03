"""tests/conftest.py — Fixtures estándar para Pytest (FastAPI + Clean Architecture)."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest

try:
    from fastapi.testclient import TestClient
    from httpx import ASGITransport, AsyncClient

    from src.main import app

    HAS_FASTAPI_TEST_DEPS = True
except ImportError:
    HAS_FASTAPI_TEST_DEPS = False


@pytest.fixture
def sync_client() -> Generator[Any, None, None]:
    if not HAS_FASTAPI_TEST_DEPS:
        pytest.skip("Dependencias de testing FastAPI no instaladas.")
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator[Any, None]:
    if not HAS_FASTAPI_TEST_DEPS:
        pytest.skip("Dependencias de testing FastAPI no instaladas.")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
