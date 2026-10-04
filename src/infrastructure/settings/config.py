"""src/infrastructure/settings/config.py — Centralización de variables de entorno."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Toda la configuración vive acá con sus valores por defecto; .env es solo para secretos."""

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

    # Mediciones: un CSV por medidor (instante, potencia_kw)
    MEDICIONES_CSV_DIR: str = Field(default="data/input")
    # Resultados del entrenamiento (no versionados)
    RESULTADOS_DIR: str = Field(default="data/output")
    # Eventos reales de los medidores simulados (la "verdad" para evaluar)
    VERDAD_DIR: str = Field(default="data/verdad")
    # Directorio para modelos serializados con joblib
    MODELOS_DIR: str = Field(default="data/models")

    # NILM
    # Umbral |ΔP| para detectar eventos. None = automático por medidor (método de Otsu);
    # un número (ej. NILM_UMBRAL_KW=60) lo fija a mano para comparar.
    NILM_UMBRAL_KW: float | None = Field(default=None)
    # Separación mínima (η de Otsu) para confiar en el umbral automático; una sola montaña da ~0.7
    NILM_SEPARACION_MINIMA: float = Field(default=0.8)
    # Radio de DBSCAN: qué tan parecidos tienen que ser dos saltos para ser la misma carga.
    # None = automático por medidor: el mayor entre Freedman–Diaconis y 2 × ruido; un número lo fija a mano.
    NILM_EPS_KW: float | None = Field(default=None)
    # Eventos mínimos para que un grupo sea una carga. None = automático: uno por día analizado
    # (al menos 3); un número lo fija a mano.
    NILM_MIN_EVENTOS: int | None = Field(default=None)
    # Proporción mínima encendidos/apagados para considerar una carga ON/OFF (0.5 = uno a lo sumo el doble del otro)
    NILM_BALANCE_MINIMO: float = Field(default=0.5)


def describir_nilm(settings: Settings) -> str:
    umbral = "automático" if settings.NILM_UMBRAL_KW is None else f"{settings.NILM_UMBRAL_KW} kW"
    radio = "automático" if settings.NILM_EPS_KW is None else f"{settings.NILM_EPS_KW} kW"
    minimo = "automático" if settings.NILM_MIN_EVENTOS is None else f"{settings.NILM_MIN_EVENTOS} eventos"
    return (
        f"Configuración NILM: umbral {umbral} · radio {radio} · "
        f"mínimo {minimo} · datos en {settings.MEDICIONES_CSV_DIR}"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
