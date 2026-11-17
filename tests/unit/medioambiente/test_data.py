"""tests/unit/medioambiente/test_data.py — Carga, limpieza de -200 y descarga del dataset UCI."""

from pathlib import Path

import pandas as pd
import pytest

from src.medioambiente.data import (
    CSV_FILENAME,
    DEFAULT_DATA_DIR,
    VALOR_FALTANTE,
    download_dataset,
    load_air_quality,
)

HEADER = (
    "Date;Time;CO(GT);PT08.S1(CO);NMHC(GT);C6H6(GT);PT08.S2(NMHC);NOx(GT);"
    "PT08.S3(NOx);NO2(GT);PT08.S4(NO2);PT08.S5(O3);T;RH;AH;;"
)
FILA_1 = "10/03/2004;18.00.00;2,6;1360;150;11,9;1046;166;1056;113;1692;1268;13,6;48,9;0,7578;;"
FILA_2 = "11/03/2004;19.00.00;-200;1292;112;9,4;1046;166;1056;113;1692;1268;-200;47,7;0,7255;;"
FILA_3 = "12/03/2004;20.00.00;0,5;1360;150;11,9;1046;166;1056;113;1692;1268;13,6;48,9;0,7578;;"
FILA_VACIA = ";" * 16


@pytest.fixture
def csv_sintetico(tmp_path: Path) -> Path:
    ruta = tmp_path / CSV_FILENAME
    ruta.write_text(
        "\n".join([HEADER, FILA_1, FILA_2, FILA_3, FILA_VACIA]) + "\n", encoding="utf-8"
    )
    return ruta


def test_load_lee_separador_y_coma_decimal(csv_sintetico: Path) -> None:
    df = load_air_quality(csv_sintetico)
    assert df.loc[0, "CO(GT)"] == pytest.approx(2.6)
    assert df.loc[0, "AH"] == pytest.approx(0.7578)
    assert df.loc[0, "Date"] == "10/03/2004"


def test_load_convierte_menos_200_en_nan(csv_sintetico: Path) -> None:
    df = load_air_quality(csv_sintetico)
    numericas = df.select_dtypes("number")
    assert not (numericas == VALOR_FALTANTE).any().any()
    assert pd.isna(df.loc[1, "CO(GT)"])
    assert pd.isna(df.loc[1, "T"])
    assert not pd.isna(df.loc[0, "CO(GT)"])


def test_load_descarta_filas_y_columnas_vacias(csv_sintetico: Path) -> None:
    df = load_air_quality(csv_sintetico)
    assert df.shape == (3, 15)
    assert not any(str(c).startswith("Unnamed") for c in df.columns)


def test_load_lanza_error_si_no_existe(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="download_dataset"):
        load_air_quality(tmp_path / "no_existe.csv")


@pytest.mark.skipif(
    not (DEFAULT_DATA_DIR / CSV_FILENAME).exists(),
    reason="Dataset local ausente: ejecutar download_dataset() primero.",
)
def test_dataset_local_real_cumple_contracto() -> None:
    df = load_air_quality()
    numericas = df.select_dtypes("number")
    assert not (numericas == VALOR_FALTANTE).any().any()
    assert len(df) > 9000
    assert {"T", "RH", "AH", "CO(GT)", "Date", "Time"} <= set(df.columns)


def test_download_dataset_no_descarga_si_ya_existe(tmp_path: Path) -> None:
    destino = tmp_path / "datos"
    destino.mkdir()
    (destino / CSV_FILENAME).write_text("Date;Time\n", encoding="utf-8")
    resultado = download_dataset(destino)
    assert resultado == destino / CSV_FILENAME
    assert resultado.read_text(encoding="utf-8") == "Date;Time\n"
