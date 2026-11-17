"""tests/integration/test_descarga_air_quality.py — Descarga real del dataset UCI #360."""

from pathlib import Path
from urllib.error import URLError

import pytest

from src.medioambiente.data import CSV_FILENAME, download_dataset, load_air_quality


def test_download_dataset_desde_uci(tmp_path: Path) -> None:
    try:
        ruta = download_dataset(tmp_path / "datos")
    except (URLError, TimeoutError, OSError) as exc:  # red no disponible
        pytest.skip(f"UCI inaccesible desde este entorno: {exc}")
    assert ruta == tmp_path / "datos" / CSV_FILENAME
    df = load_air_quality(ruta)
    assert len(df) > 9000
    assert {"T", "RH", "AH", "CO(GT)"} <= set(df.columns)
