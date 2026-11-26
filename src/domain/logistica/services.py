"""src/domain/logistica/services.py — Reglas puras: anti-fuga y lectura de negocio de los grupos."""

from __future__ import annotations

from src.domain.logistica.exceptions import FugaDeDatosError
from src.domain.logistica.value_objects import FORBIDDEN_COLUMNS


def validate_no_data_leakage(feature_columns: list[str] | tuple[str, ...]) -> None:
    """Verifica que ninguna variable prohibida (fuga de datos) esté presente en X."""
    forbidden_set = {col.lower().strip() for col in FORBIDDEN_COLUMNS}
    leaked = [col for col in feature_columns if col.lower().strip() in forbidden_set]
    if leaked:
        raise FugaDeDatosError(leaked)


def describe_cluster_business_profile(
    scheduled_days_mean: float,
    quantity_mean: float,
    latitude_mean: float,
) -> str:
    """Genera una descripción en lenguaje de negocio según los centroides del grupo."""
    hub = "Hub Caribe (PR)" if latitude_mean < 25.0 else "Hub EE.UU. Continental"
    if quantity_mean >= 3.5:
        return f"Pedidos mayoristas de alto volumen y alto ticket ({hub})"
    if scheduled_days_mean <= 2.0:
        return f"Envíos rápidos/urgentes (1-2 días programados) desde {hub}"
    return f"Envíos estándar (4 días programados) de bajo volumen desde {hub}"
