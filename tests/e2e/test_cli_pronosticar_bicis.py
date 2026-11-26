"""tests/e2e/test_cli_pronosticar_bicis.py — CLI temporal con ZIP sintéticos."""

from __future__ import annotations

import csv
import io
import sys
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pytest

import src.infrastructure.bicis.descargar_datasets as modulo_descarga
from src.infrastructure.cli.pronosticar_bicis import main


def _crear_zip_sintetico(destino: Path, anio: int) -> None:
    contenido = io.StringIO(newline="")
    escritor = csv.writer(contenido)
    escritor.writerow(["id_recorrido", "fecha_origen_recorrido"])
    fecha = date(anio, 1, 1)
    while fecha.year == anio:
        escritor.writerow([f"{anio}-{fecha.isoformat()}", f"{fecha.isoformat()}T08:00:00"])
        fecha += timedelta(days=1)

    ruta = destino / f"recorridos-realizados-{anio}.zip"
    with zipfile.ZipFile(ruta, "w", compression=zipfile.ZIP_DEFLATED) as archivo_zip:
        archivo_zip.writestr(f"recorridos-{anio}.csv", contenido.getvalue())


def _rechazar_descarga(*args: object, **kwargs: object) -> None:
    raise AssertionError("El CLI intentó descargar aunque los ZIP sintéticos ya existían.")


def test_cli_acepta_directorio_y_evalua_zip_sinteticos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    for anio in (2024, 2025):
        _crear_zip_sintetico(tmp_path, anio)

    monkeypatch.setattr(sys, "argv", ["pronosticar_bicis", "--directorio-datos", str(tmp_path)])
    monkeypatch.setattr(modulo_descarga, "urlopen", _rechazar_descarga)

    with caplog.at_level("INFO", logger="backend-api"):
        main()
    salida = caplog.text
    assert "Muestras: 359 días de entrenamiento (2024), 365 de prueba (2025)" in salida
    assert "Mismo día de la semana anterior" in salida
    assert "Random Forest" in salida
