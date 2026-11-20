"""src/infrastructure/sklearn/mantenimiento_descarga.py — Descarga del dataset AI4I 2020 (UCI, CC BY 4.0) al directorio local ignorado por git."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from urllib.request import urlopen

from src.infrastructure.sklearn.mantenimiento_datos import DEFAULT_CSV_PATH

DATASET_URL: str = (
    "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip"
)
TIMEOUT_SECONDS: int = 60


def download_dataset(url: str = DATASET_URL, destination: Path = DEFAULT_CSV_PATH) -> Path:
    """Descarga el zip, extrae su único CSV y lo guarda en destination."""
    with urlopen(url, timeout=TIMEOUT_SECONDS) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
    if len(csv_names) != 1:
        raise ValueError(f"Se esperaba un único CSV en el zip, hay: {csv_names}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(archive.read(csv_names[0]))
    return destination
