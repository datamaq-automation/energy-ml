"""src/adapters/logistica/gateways/pedidos_csv_gateway.py — Pedidos del export DataCo Supply Chain.

Implementa el puerto RepositorioPedidos: lee el CSV (latin-1), desglosa la fecha
del pedido y elimina las columnas que no existen al momento de despachar.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.domain.logistica.services import validate_no_data_leakage
from src.domain.logistica.value_objects import FORBIDDEN_COLUMNS, TARGET_COLUMN


def load_and_prepare_orders(csv_path: Path, max_rows: int | None = None) -> pd.DataFrame:
    """Carga el CSV de pedidos, desglosa la fecha del pedido y elimina columnas prohibidas."""
    df = pd.read_csv(csv_path, encoding="latin-1", nrows=max_rows)
    order_dt = pd.to_datetime(df["order date (DateOrders)"], format="mixed")
    df["order_month"] = order_dt.dt.month
    df["order_dayofweek"] = order_dt.dt.day_of_week
    df["order_hour"] = order_dt.dt.hour

    drop_cols = [c for c in FORBIDDEN_COLUMNS if c != TARGET_COLUMN and c in df.columns]
    cleaned = df.drop(columns=drop_cols)
    feature_cols = [c for c in cleaned.columns if c != TARGET_COLUMN]
    validate_no_data_leakage(feature_cols)
    return cleaned


class PedidosCsvGateway:
    """Fuente de pedidos desde un CSV local (el dataset de Kaggle no se versiona)."""

    def __init__(self, csv_path: Path, max_rows: int | None = None) -> None:
        self._csv_path = csv_path
        self._max_rows = max_rows

    def cargar(self) -> pd.DataFrame:
        """Devuelve los pedidos sin columnas con fuga de datos."""
        return load_and_prepare_orders(self._csv_path, max_rows=self._max_rows)
