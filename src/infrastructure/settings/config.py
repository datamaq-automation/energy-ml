"""src/infrastructure/settings/config.py — Centralización de variables de entorno."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Entorno
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")

    # API
    PROJECT_NAME: str = Field(default="backend-api")
    VERSION: str = Field(default="1.0.0")
    API_V1_PREFIX: str = Field(default="/api/v1")
    ALLOWED_HOSTS: list[str] = Field(default_factory=lambda: ["*"])

    # Seguridad
    SECRET_KEY: str = Field(default="change-this-insecure-secret-key-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    # Mediciones: un CSV por medidor (instante, potencia_kw)
    MEDICIONES_CSV_DIR: str = Field(default="data/input")

    # NILM (valores iniciales derivados del análisis de la planta UPP)
    NILM_UMBRAL_KW: float = Field(default=60.0)
    NILM_EPS_KW: float = Field(default=8.0)
    NILM_MIN_EVENTOS: int = Field(default=10)


@lru_cache
def get_settings() -> Settings:
    return Settings()
