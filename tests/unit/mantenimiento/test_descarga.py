"""tests/unit/mantenimiento/test_descarga.py — Pruebas de la descarga del dataset de mantenimiento, sin internet."""

import zipfile
from pathlib import Path

import pytest

from src.infrastructure.sklearn.mantenimiento_descarga import download_dataset


def test_download_extracts_the_csv(tmp_path: Path) -> None:
    source = tmp_path / "fuente.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("ai4i2020.csv", "UDI,Machine failure\n1,0\n")
    destination = tmp_path / "datos" / "mantenimiento" / "ai4i2020.csv"
    result = download_dataset(source.as_uri(), destination)
    assert result == destination
    assert destination.read_text().startswith("UDI")


def test_download_rejects_zip_without_a_single_csv(tmp_path: Path) -> None:
    source = tmp_path / "fuente.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("a.csv", "x\n")
        archive.writestr("b.csv", "y\n")
    with pytest.raises(ValueError):
        download_dataset(source.as_uri(), tmp_path / "salida.csv")
