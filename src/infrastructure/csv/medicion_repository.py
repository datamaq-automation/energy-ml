"""src/infrastructure/csv/medicion_repository.py — Lectura de potencia desde data/input/<medidor>.csv."""

import csv
from datetime import datetime
from pathlib import Path

from src.domain.cargas.entities import Medicion


class CsvMedicionRepository:
    """Implementa MedicionRepository sobre CSV con columnas instante,potencia_kw (ya en kW)."""

    def __init__(self, carpeta: Path) -> None:
        self._carpeta = carpeta

    def medidores(self) -> list[str]:
        return sorted(p.stem for p in self._carpeta.glob("*.csv"))

    def listar(self, medidor: str, desde: datetime, hasta: datetime) -> list[Medicion]:
        # Solo nombres de archivos existentes: evita leer rutas arbitrarias ("../.env").
        if medidor not in self.medidores():
            raise LookupError(f"Medidor desconocido: {medidor}")
        with (self._carpeta / f"{medidor}.csv").open(encoding="utf-8") as archivo:
            filas = (
                Medicion(instante=datetime.fromisoformat(f["instante"]), potencia_kw=float(f["potencia_kw"]))
                for f in csv.DictReader(archivo)
            )
            return [m for m in filas if desde <= m.instante < hasta]
