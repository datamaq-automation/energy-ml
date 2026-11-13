"""Endpoint de salud del módulo SIBO."""

from __future__ import annotations

from fastapi import APIRouter

from sibo.application.dtos import SaludResponse

router = APIRouter(tags=["Salud"])

VERSION = "1.0.0"


@router.get("/salud", response_model=SaludResponse)
def salud() -> SaludResponse:
    return SaludResponse(status="ok", modulo="sibo", version=VERSION)
