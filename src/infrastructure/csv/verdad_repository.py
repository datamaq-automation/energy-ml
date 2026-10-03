"""src/infrastructure/csv/verdad_repository.py — Eventos reales en <carpeta>/<medidor>.csv (instante,delta_kw,carga_kw)."""

import csv
from datetime import datetime
from pathlib import Path

from src.domain.cargas.entities import EventoReal
from src.infrastructure.settings.logger import logger


class CsvVerdadRepository:
    """Implementa VerdadRepository: un CSV por medidor simulado."""

    def __init__(self, carpeta: Path) -> None:
        self._carpeta = carpeta

    def medidores(self) -> list[str]:
        return sorted(p.stem for p in self._carpeta.glob("*.csv"))

    def guardar(self, medidor: str, eventos: list[EventoReal]) -> None:
        self._carpeta.mkdir(parents=True, exist_ok=True)
        destino = self._carpeta / f"{medidor}.csv"
        with destino.open("w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["instante", "delta_kw", "carga_kw"])
            escritor.writerows((e.instante.isoformat(), e.delta_kw, e.carga_kw) for e in eventos)
        logger.info("%d eventos reales guardados en %s", len(eventos), destino)

    def listar(self, medidor: str) -> list[EventoReal]:
        if medidor not in self.medidores():
            raise LookupError(f"No hay verdad conocida para {medidor}: solo para medidores simulados")
        with (self._carpeta / f"{medidor}.csv").open(encoding="utf-8") as archivo:
            return [
                EventoReal(
                    instante=datetime.fromisoformat(f["instante"]),
                    delta_kw=float(f["delta_kw"]),
                    carga_kw=float(f["carga_kw"]),
                )
                for f in csv.DictReader(archivo)
            ]
