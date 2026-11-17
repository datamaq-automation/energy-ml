"""src/medioambiente/data.py — Descarga y carga del dataset Air Quality (UCI #360)."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

from src.infrastructure.settings.logger import logger

UCI_ZIP_URL = "https://archive.ics.uci.edu/static/public/360/air+quality.zip"
CSV_FILENAME = "AirQualityUCI.csv"
DEFAULT_DATA_DIR = Path("datos/medioambiente")
VALOR_FALTANTE = -200  # Código de faltante del dataset (no es una medición real).
COLUMNAS_ESPERADAS = (
    "Date",
    "Time",
    "CO(GT)",
    "PT08.S1(CO)",
    "NMHC(GT)",
    "C6H6(GT)",
    "PT08.S2(NMHC)",
    "NOx(GT)",
    "PT08.S3(NOx)",
    "NO2(GT)",
    "PT08.S4(NO2)",
    "PT08.S5(O3)",
    "T",
    "RH",
    "AH",
)


def download_dataset(destino: Path = DEFAULT_DATA_DIR, sobrescribir: bool = False) -> Path:
    """Descarga el zip de UCI y extrae AirQualityUCI.csv dentro de `destino`.

    Si el CSV ya existe y `sobrescribir` es False, no vuelve a descargar.
    """
    destino.mkdir(parents=True, exist_ok=True)
    destino_csv = destino / CSV_FILENAME
    if destino_csv.exists() and not sobrescribir:
        logger.info("Dataset ya presente en %s; se omite la descarga.", destino_csv)
        return destino_csv
    logger.info("Descargando Air Quality desde %s", UCI_ZIP_URL)
    with urlopen(UCI_ZIP_URL, timeout=60) as respuesta:
        contenido = respuesta.read()
    with zipfile.ZipFile(io.BytesIO(contenido)) as archivo_zip:
        with archivo_zip.open(CSV_FILENAME) as origen, destino_csv.open("wb") as salida:
            salida.write(origen.read())
    logger.info("Dataset extraído en %s (%d bytes)", destino_csv, destino_csv.stat().st_size)
    return destino_csv


def load_air_quality(ruta: Path | None = None) -> pd.DataFrame:
    """Lee el CSV (separador ';', coma decimal), convierte -200 a NaN y descarta filas/columnas vacías.

    Lanza FileNotFoundError si el archivo no existe (ver download_dataset).
    """
    csv_path = ruta if ruta is not None else DEFAULT_DATA_DIR / CSV_FILENAME
    if not csv_path.exists():
        raise FileNotFoundError(
            f"No se encontró {csv_path}. Ejecutá download_dataset() para obtenerlo."
        )
    df = pd.read_csv(csv_path, sep=";", decimal=",")
    filas_antes, columnas_antes = df.shape
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    df = df.replace(VALOR_FALTANTE, float("nan"))
    if (df == VALOR_FALTANTE).any().any():  # pragma: no cover - defensa redundante
        raise ValueError(f"Quedaron valores {VALOR_FALTANTE} tras la limpieza de {csv_path}")
    columnas_faltantes = [c for c in COLUMNAS_ESPERADAS if c not in df.columns]
    if columnas_faltantes:
        raise ValueError(
            f"El archivo {csv_path} no tiene las columnas esperadas: {columnas_faltantes}"
        )
    logger.info(
        "Air Quality cargado: %d filas x %d columnas "
        "(descartadas %d filas vacías y %d columnas vacías)",
        df.shape[0],
        df.shape[1],
        filas_antes - df.shape[0],
        columnas_antes - df.shape[1],
    )
    return df
