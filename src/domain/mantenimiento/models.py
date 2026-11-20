"""src/domain/mantenimiento/models.py — Columnas permitidas y regla anti-fuga de datos para mantenimiento."""

from __future__ import annotations

from collections.abc import Iterable

TARGET_COLUMN: str = "Machine failure"

FORBIDDEN_COLUMNS: tuple[str, ...] = (
    "Machine failure",
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF",
    "UDI",
    "Product ID",
)

NUMERIC_FEATURES: tuple[str, ...] = (
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
)

CATEGORICAL_FEATURES: tuple[str, ...] = ("Type",)


def validate_no_data_leakage(feature_columns: Iterable[str]) -> None:
    """Falla si alguna columna prohibida (modo de falla, etiqueta o id) entra como entrada."""
    leaked = sorted(set(feature_columns) & set(FORBIDDEN_COLUMNS))
    if leaked:
        raise ValueError(f"Columnas prohibidas en X (fuga de datos): {leaked}")
