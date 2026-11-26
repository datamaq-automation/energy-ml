"""tests/integration/test_bicis_repository.py — Adaptación de ZIP a totales diarios."""

import csv
import io
import zipfile
from datetime import date
from pathlib import Path

import pytest

from src.adapters.bicis.gateways.repositorio_recorridos_gateway import (
    RepositorioRecorridosBicis,
)


def crear_zip(ruta: Path, nombre_csv: str, filas: list[tuple[str, str]]) -> Path:
    contenido = io.StringIO(newline="")
    escritor = csv.writer(contenido)
    escritor.writerow(["Id_recorrido", "fecha_origen_recorrido"])
    escritor.writerows(filas)
    with zipfile.ZipFile(ruta, "w", compression=zipfile.ZIP_DEFLATED) as archivo:
        archivo.writestr(nombre_csv, contenido.getvalue())
    return ruta


def test_repositorio_agrega_por_fecha_y_no_completa_dias_sin_viajes(tmp_path: Path) -> None:
    archivo = crear_zip(
        tmp_path / "2024.zip",
        "Trips.csv",
        [("1", "2024-01-01T10:00:00"), ("2", "2024-01-01T11:00:00")],
    )
    repositorio = RepositorioRecorridosBicis({2024: archivo})

    serie = repositorio.obtener(date(2024, 1, 1), date(2024, 1, 2))

    assert [(dia.fecha, dia.viajes) for dia in serie.dias] == [(date(2024, 1, 1), 2)]
    assert serie.dias_faltantes(date(2024, 1, 1), date(2024, 1, 2)) == (date(2024, 1, 2),)
    assert repositorio.calidad.filas_leidas == 2


def test_repositorio_descarta_ids_duplicados_con_la_misma_fecha(tmp_path: Path) -> None:
    archivo = crear_zip(
        tmp_path / "2024.zip",
        "trips.csv",
        [("1", "2024-01-01T10:00:00"), ("1", "2024-01-01T10:00:00")],
    )
    repositorio = RepositorioRecorridosBicis({2024: archivo})

    serie = repositorio.obtener(date(2024, 1, 1), date(2024, 1, 1))

    assert [(dia.fecha, dia.viajes) for dia in serie.dias] == [(date(2024, 1, 1), 1)]
    assert repositorio.calidad.viajes_duplicados == 1


def test_repositorio_rechaza_id_duplicado_con_fecha_distinta(tmp_path: Path) -> None:
    archivo = crear_zip(
        tmp_path / "2024.zip",
        "trips.csv",
        [("1", "2024-01-01T10:00:00"), ("1", "2024-01-02T10:00:00")],
    )
    repositorio = RepositorioRecorridosBicis({2024: archivo})

    with pytest.raises(ValueError, match="duplicados conflictivos=1"):
        repositorio.obtener(date(2024, 1, 1), date(2024, 1, 2))


def test_repositorio_rechaza_fecha_de_origen_invalida(tmp_path: Path) -> None:
    archivo = crear_zip(tmp_path / "2024.zip", "trips.csv", [("1", "fecha-inválida")])
    repositorio = RepositorioRecorridosBicis({2024: archivo})

    with pytest.raises(ValueError, match="fechas inválidas=1"):
        repositorio.obtener(date(2024, 1, 1), date(2024, 1, 1))
