"""src/infrastructure/csv/venta_repository.py — Lee las ventas diarias desde un CSV (date, store, item, sales)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.domain.ventas.modelos import COLUMNAS_VENTAS
from src.infrastructure.settings.logger import logger


class CsvVentaRepository:
    """Implementa FuenteVentas: lee el CSV una sola vez y entrega una copia en cada pedido."""

    def __init__(self, ruta: Path) -> None:
        self._ruta = ruta
        self._ventas: pd.DataFrame | None = None

    def leer(self) -> pd.DataFrame:
        """Devuelve la tabla de ventas con la fecha convertida y ordenada por serie y día."""
        if self._ventas is None:
            ventas = pd.read_csv(self._ruta)
            faltan = [c for c in COLUMNAS_VENTAS if c not in ventas.columns]
            if faltan:
                raise ValueError(f"Al CSV {self._ruta} le faltan las columnas {faltan}.")
            ventas["date"] = pd.to_datetime(ventas["date"])
            self._ventas = ventas.sort_values(["store", "item", "date"]).reset_index(drop=True)
            logger.info("Ventas leídas: %d filas desde %s", len(self._ventas), self._ruta)
        return self._ventas.copy()
