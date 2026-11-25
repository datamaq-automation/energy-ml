"""src/infrastructure/csv/observaciones_repository.py ? Implementaci?n del m?dulo."""

import csv
from collections import defaultdict
from datetime import date, datetime, time
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo

from src.domain.crecidas.modelos import NivelRio
from src.infrastructure.settings.logger import logger

ZONA_HORARIA = ZoneInfo("America/Argentina/Buenos_Aires")

ARCHIVOS_ESTACIONES = {
    "tigre": "tigre_49.csv",
    "san_fernando": "san_fernando_52.csv",
}


class CsvObservacionesRepository:
    """Lee observaciones INA y las agrupa por día calendario argentino."""

    def __init__(self, carpeta: Path) -> None:
        self._carpeta = carpeta

    def estaciones(self) -> list[str]:
        """Devuelve las estaciones configuradas cuyos archivos existen."""
        return sorted(
            nombre
            for nombre, archivo in ARCHIVOS_ESTACIONES.items()
            if (self._carpeta / archivo).is_file()
        )

    def listar(
        self,
        estacion: str,
        desde: datetime,
        hasta: datetime,
    ) -> list[NivelRio]:
        """Devuelve la mediana diaria de una estación en el intervalo [desde, hasta)."""
        if estacion not in ARCHIVOS_ESTACIONES:
            raise LookupError(f"Estación desconocida: {estacion}")

        ruta = self._carpeta / ARCHIVOS_ESTACIONES[estacion]
        if not ruta.is_file():
            raise FileNotFoundError(f"No se encontró el archivo: {ruta}")

        logger.info("Leyendo observaciones de %s desde %s", estacion, ruta)

        valores_por_dia: dict[date, list[float]] = defaultdict(list)

        with ruta.open(encoding="utf-8", newline="") as archivo:
            for fila in csv.DictReader(archivo):
                instante_utc = datetime.fromisoformat(
                    fila["timestart"].replace("Z", "+00:00")
                )
                instante_local = instante_utc.astimezone(ZONA_HORARIA)
                valor = float(fila["valor"])

                if desde <= instante_local.replace(tzinfo=None) < hasta:
                    valores_por_dia[instante_local.date()].append(valor)

        observaciones = [
            NivelRio(
                instante=datetime.combine(
                    dia,
                    time.min,
                    tzinfo=ZONA_HORARIA,
                ),
                nivel_m=median(valores),
            )
            for dia, valores in sorted(valores_por_dia.items())
        ]

        logger.info(
            "%s: %d días con observaciones entre %s y %s",
            estacion,
            len(observaciones),
            desde,
            hasta,
        )
        return observaciones
