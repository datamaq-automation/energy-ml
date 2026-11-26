"""tests/unit/bicis/test_descargar_datasets.py"""

import zipfile
from pathlib import Path

import pytest

from src.infrastructure.bicis.descargar_datasets import (
    URLS_OFICIALES,
    _es_url_oficial,
    descargar_datasets,
)


def test_descargar_reutiliza_archivos_zip_validos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for anio in URLS_OFICIALES:
        ruta = tmp_path / f"recorridos-realizados-{anio}.zip"
        with zipfile.ZipFile(ruta, "w") as archivo:
            archivo.writestr("trips.csv", "id_recorrido,fecha_origen_recorrido\n")

    def descarga_inesperada(*args: object, **kwargs: object) -> None:
        raise AssertionError("No debería descargar si los ZIP locales son válidos.")

    monkeypatch.setattr("src.infrastructure.bicis.descargar_datasets.urlopen", descarga_inesperada)

    assert descargar_datasets(tmp_path) == {
        anio: tmp_path / f"recorridos-realizados-{anio}.zip" for anio in URLS_OFICIALES
    }


def test_solo_acepta_el_host_oficial_por_https() -> None:
    assert _es_url_oficial("https://cdn.buenosaires.gob.ar/recurso.zip")
    assert not _es_url_oficial("http://cdn.buenosaires.gob.ar/recurso.zip")
    assert not _es_url_oficial("https://cdn.buenosaires.gob.ar.ejemplo.org/recurso.zip")
