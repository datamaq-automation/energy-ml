"""src/infrastructure/csv/carga_repository.py — Escritura de cargas identificadas en <carpeta>/cargas_<medidor>.csv."""

import csv
from pathlib import Path

from src.domain.cargas.entities import Carga
from src.infrastructure.settings.logger import logger

COLUMNAS = ["potencia_tipica_kw", "encendidos", "apagados", "ciclos"]


class CsvCargaRepository:
    """Implementa CargaRepository: un CSV por medidor, una fila por carga."""

    def __init__(self, carpeta: Path) -> None:
        self._carpeta = carpeta

    def guardar(self, medidor: str, cargas: list[Carga]) -> None:
        self._carpeta.mkdir(parents=True, exist_ok=True)
        destino = self._carpeta / f"cargas_{medidor}.csv"
        with destino.open("w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(COLUMNAS)
            escritor.writerows(
                (c.potencia_tipica_kw, c.encendidos, c.apagados, c.ciclos) for c in cargas
            )
        logger.info("%s: %d cargas guardadas en %s", medidor, len(cargas), destino)
