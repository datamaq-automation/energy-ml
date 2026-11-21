"""src/adapters/bicis/repositorio_recorridos.py — Adaptador de ZIP oficiales a totales diarios."""

from __future__ import annotations

import csv
import io
import sqlite3
import tempfile
import zipfile
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from src.domain.bicis.modelos import DiaViajes, SerieDiariaViajes

ANIOS_DISPONIBLES: tuple[int, ...] = (2024, 2025)


@dataclass(frozen=True)
class CalidadDatosRecorridos:
    """Conteos de control calculados sin conservar filas individuales."""

    filas_leidas: int
    viajes_duplicados: int
    duplicados_conflictivos: int
    ids_ausentes: int
    fechas_invalidas: int
    filas_malformadas: int


class RepositorioRecorridosBicis:
    """Implementa el puerto diario leyendo solo ID y fecha de origen desde ZIP/CSV."""

    def __init__(self, archivos: Mapping[int, Path]) -> None:
        self._archivos = dict(archivos)
        self._calidad: CalidadDatosRecorridos | None = None

    @property
    def calidad(self) -> CalidadDatosRecorridos:
        """Calidad de la última lectura; requiere haber ejecutado obtener()."""
        if self._calidad is None:
            raise RuntimeError("La calidad todavía no está disponible; primero ejecutá obtener().")
        return self._calidad

    def obtener(self, desde: date, hasta: date) -> SerieDiariaViajes:
        """Agrega viajes dentro del intervalo inclusivo y rechaza datos ambiguos."""
        if desde > hasta:
            raise ValueError("La fecha inicial no puede ser posterior a la fecha final.")

        anios = range(
            max(ANIOS_DISPONIBLES[0], desde.year), min(ANIOS_DISPONIBLES[-1], hasta.year) + 1
        )
        faltantes = [anio for anio in anios if anio not in self._archivos]
        if faltantes:
            raise FileNotFoundError(f"Faltan los ZIP oficiales de estos años: {faltantes}.")
        if not anios:
            raise ValueError("El repositorio solo dispone de recorridos de 2024 y 2025.")

        conteos: Counter[date] = Counter()
        totales = [0, 0, 0, 0, 0, 0]
        with tempfile.TemporaryDirectory(prefix="bicis-ids-") as temporal:
            conexion = sqlite3.connect(Path(temporal) / "ids.sqlite3")
            try:
                conexion.execute("PRAGMA journal_mode=OFF")
                conexion.execute("PRAGMA synchronous=OFF")
                conexion.execute(
                    "CREATE TABLE ids (anio INTEGER, id TEXT, fecha TEXT, "
                    "PRIMARY KEY (anio, id)) WITHOUT ROWID"
                )
                for anio in anios:
                    resultados = self._leer_archivo(
                        self._archivos[anio], anio, desde, hasta, conteos, conexion
                    )
                    totales = [
                        acumulado + nuevo
                        for acumulado, nuevo in zip(totales, resultados, strict=True)
                    ]
                conexion.commit()
            finally:
                conexion.close()

        self._calidad = CalidadDatosRecorridos(*totales)
        if any(
            (
                self._calidad.duplicados_conflictivos,
                self._calidad.ids_ausentes,
                self._calidad.fechas_invalidas,
                self._calidad.filas_malformadas,
            )
        ):
            raise ValueError(
                "No se genera la serie: revisar calidad del origen "
                f"(duplicados={self._calidad.viajes_duplicados}, "
                f"duplicados conflictivos={self._calidad.duplicados_conflictivos}, "
                f"IDs ausentes={self._calidad.ids_ausentes}, "
                f"fechas inválidas={self._calidad.fechas_invalidas}, "
                f"filas malformadas={self._calidad.filas_malformadas})."
            )
        if not conteos:
            raise ValueError(f"No hay viajes observados entre {desde} y {hasta}.")

        return SerieDiariaViajes(
            tuple(DiaViajes(fecha, conteos[fecha]) for fecha in sorted(conteos))
        )

    @staticmethod
    def _leer_archivo(
        ruta: Path,
        anio: int,
        desde: date,
        hasta: date,
        conteos: Counter[date],
        conexion: sqlite3.Connection,
    ) -> tuple[int, int, int, int, int, int]:
        totales = [0, 0, 0, 0, 0, 0]
        with zipfile.ZipFile(ruta) as archivo_zip:
            nombre_csv = _nombre_csv(archivo_zip, ruta)
            with archivo_zip.open(nombre_csv) as binario:
                texto = io.TextIOWrapper(
                    binario, encoding="utf-8-sig", errors="replace", newline=""
                )
                lector = csv.DictReader(texto)
                id_columna, fecha_columna = _columnas_requeridas(lector.fieldnames, ruta)
                for fila in lector:
                    _procesar_fila(
                        fila,
                        anio,
                        desde,
                        hasta,
                        id_columna,
                        fecha_columna,
                        conteos,
                        conexion,
                        totales,
                    )
        return tuple(totales)


def _nombre_csv(archivo_zip: zipfile.ZipFile, ruta: Path) -> str:
    csvs = [nombre for nombre in archivo_zip.namelist() if nombre.lower().endswith(".csv")]
    if len(csvs) != 1:
        raise ValueError(f"{ruta} debe contener exactamente un CSV (encontrados: {len(csvs)}).")
    return csvs[0]


def _columnas_requeridas(fieldnames: list[str] | None, ruta: Path) -> tuple[str, str]:
    columnas = {
        nombre.replace("\ufeff", "").strip().casefold(): nombre for nombre in fieldnames or []
    }
    id_columna = columnas.get("id_recorrido")
    fecha_columna = columnas.get("fecha_origen_recorrido")
    if id_columna is None or fecha_columna is None:
        raise ValueError(f"{ruta} no contiene id_recorrido y fecha_origen_recorrido.")
    return id_columna, fecha_columna


def _procesar_fila(
    fila: Mapping[str | None, str | None],
    anio: int,
    desde: date,
    hasta: date,
    id_columna: str,
    fecha_columna: str,
    conteos: Counter[date],
    conexion: sqlite3.Connection,
    totales: list[int],
) -> None:
    totales[0] += 1
    if None in fila:
        totales[5] += 1
        return
    try:
        fecha = datetime.fromisoformat((fila.get(fecha_columna) or "").strip()).date()
    except ValueError:
        totales[4] += 1
        return

    identificador = (fila.get(id_columna) or "").strip()
    if not identificador:
        totales[3] += 1
    elif not _registrar_identificador(conexion, anio, identificador, fecha, totales):
        return
    if desde <= fecha <= hasta:
        conteos[fecha] += 1


def _registrar_identificador(
    conexion: sqlite3.Connection,
    anio: int,
    identificador: str,
    fecha: date,
    totales: list[int],
) -> bool:
    insertado = conexion.execute(
        "INSERT OR IGNORE INTO ids (anio, id, fecha) VALUES (?, ?, ?)",
        (anio, identificador, fecha.isoformat()),
    )
    if insertado.rowcount != 0:
        return True

    totales[1] += 1
    fecha_original = conexion.execute(
        "SELECT fecha FROM ids WHERE anio = ? AND id = ?",
        (anio, identificador),
    ).fetchone()[0]
    if fecha_original != fecha.isoformat():
        totales[2] += 1
    return False
