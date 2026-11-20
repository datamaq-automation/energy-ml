"""src/infrastructure/bicis/descargar_datasets.py — Descarga ZIP oficiales en una carpeta ignorada."""

from __future__ import annotations

import shutil
import zipfile
from http.client import HTTPException
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

DIRECTORIO_DATOS: Path = Path("datos/bicis")
HOST_OFICIAL: str = "cdn.buenosaires.gob.ar"
URLS_OFICIALES: dict[int, str] = {
    2024: (
        "https://cdn.buenosaires.gob.ar/datosabiertos/datasets/transporte-y-obras-publicas/"
        "bicicletas-publicas/recorridos-realizados-2024.zip"
    ),
    2025: (
        "https://cdn.buenosaires.gob.ar/datosabiertos/datasets/transporte-y-obras-publicas/"
        "bicicletas-publicas/recorridos-realizados-2025.zip"
    ),
}


def descargar_datasets(destino: Path = DIRECTORIO_DATOS) -> dict[int, Path]:
    """Descarga los recursos oficiales faltantes y reutiliza ZIP locales válidos."""
    destino.mkdir(parents=True, exist_ok=True)
    archivos: dict[int, Path] = {}
    for anio, url in URLS_OFICIALES.items():
        ruta = destino / f"recorridos-realizados-{anio}.zip"
        if not ruta.is_file() or not zipfile.is_zipfile(ruta):
            _descargar_zip(url, ruta)
        archivos[anio] = ruta
    return archivos


def _descargar_zip(url: str, destino: Path) -> None:
    """Descarga por bloques, reanuda archivos parciales y solo acepta el host oficial."""
    if not _es_url_oficial(url):
        raise ValueError(f"URL no oficial rechazada: {url}")
    parcial = destino.with_suffix(destino.suffix + ".part")
    for intento in range(3):
        if parcial.is_file() and zipfile.is_zipfile(parcial):
            parcial.replace(destino)
            return
        posicion = parcial.stat().st_size if parcial.exists() else 0
        encabezados = {"Range": f"bytes={posicion}-"} if posicion else {}
        solicitud = Request(url, headers=encabezados)
        try:
            _descargar_tramo(solicitud, parcial, posicion)
        except (HTTPException, URLError, TimeoutError, OSError):
            if intento == 2:
                raise
        if zipfile.is_zipfile(parcial):
            parcial.replace(destino)
            return
    raise ValueError(f"Descarga incompleta o inválida: {parcial}.")


def _descargar_tramo(solicitud: Request, parcial: Path, posicion: int) -> None:
    with urlopen(solicitud, timeout=120) as respuesta:
        if not _es_url_oficial(respuesta.geturl()):
            raise ValueError(f"Redirección fuera del host oficial rechazada: {respuesta.geturl()}")
        reanudar = posicion > 0 and respuesta.status == 206
        if reanudar and not (respuesta.headers.get("Content-Range") or "").startswith(
            f"bytes {posicion}-"
        ):
            raise ValueError("El servidor respondió un rango distinto al solicitado.")
        if respuesta.status == 206 and not reanudar:
            raise ValueError("El servidor devolvió una descarga parcial inesperada.")
        with parcial.open("ab" if reanudar else "wb") as salida:
            shutil.copyfileobj(respuesta, salida, length=1024 * 1024)


def _es_url_oficial(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname == HOST_OFICIAL
