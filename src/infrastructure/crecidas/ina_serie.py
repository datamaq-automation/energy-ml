"""src/infrastructure/crecidas/ina_serie.py — Cliente de series de altura hidrométrica del INA (alerta5)."""

from __future__ import annotations

import csv
import io
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import date, datetime

from src.domain.crecidas.modelos import NivelRio

BASE_URL = "https://alerta.ina.gob.ar/a5/getObservaciones"
SERIE_TIGRE_ALTURA_DIARIA = 49
SERIE_SAN_FERNANDO_ALTURA_HORARIA = 52


def construir_url(serie_id: int, desde: date, hasta: date) -> str:
    """Arma la URL pública de descarga CSV de una serie puntual del INA."""
    query = urllib.parse.urlencode(
        {
            "tipo": "puntual",
            "series_id": serie_id,
            "timestart": desde.isoformat(),
            "timeend": hasta.isoformat(),
            "format": "csv",
        }
    )
    return f"{BASE_URL}?{query}"


def parsear_csv(texto: str) -> list[NivelRio]:
    """Convierte el CSV del INA en NivelRio ordenados por instante.

    Descarta filas sin valor. Los instantes llegan en UTC (sufijo Z).
    """
    niveles: list[NivelRio] = []
    for fila in csv.DictReader(io.StringIO(texto)):
        valor = (fila.get("valor") or "").strip()
        marca = (fila.get("timestart") or "").strip()
        if not valor or not marca:
            continue
        instante = datetime.fromisoformat(marca.replace("Z", "+00:00"))
        niveles.append(NivelRio(instante=instante, nivel_m=float(valor)))
    niveles.sort(key=lambda nivel: nivel.instante)
    return niveles


def descargar_texto(url: str) -> str:
    """Descarga el contenido de una URL como texto UTF-8."""
    with urllib.request.urlopen(url, timeout=60) as respuesta:
        return respuesta.read().decode("utf-8")


def obtener_serie(
    serie_id: int,
    desde: date,
    hasta: date,
    descargar: Callable[[str], str] = descargar_texto,
) -> list[NivelRio]:
    """Descarga y parsea una serie. `descargar` es inyectable para tests sin red."""
    return parsear_csv(descargar(construir_url(serie_id, desde, hasta)))
