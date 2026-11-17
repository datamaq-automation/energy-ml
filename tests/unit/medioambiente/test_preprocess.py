"""tests/unit/medioambiente/test_preprocess.py — Etiqueta `episodio` a partir de CO(GT)."""

import pandas as pd

from src.medioambiente.preprocess import COLUMNA_ETIQUETA, construir_etiqueta


def _df_ejemplo() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CO(GT)": [2.6, 2.5, 0.5, float("nan"), 4.0],
            "T": [13.6, 13.3, 13.6, 12.1, 20.0],
        }
    )


def test_etiqueta_descarta_filas_sin_co() -> None:
    df = construir_etiqueta(_df_ejemplo())
    assert len(df) == 4
    assert not df["CO(GT)"].isna().any()


def test_etiqueta_umbral_inclusivo() -> None:
    df = construir_etiqueta(_df_ejemplo())
    assert df[COLUMNA_ETIQUETA].tolist() == [1, 1, 0, 1]
    assert df[COLUMNA_ETIQUETA].dtype == "int8"


def test_etiqueta_umbral_personalizado() -> None:
    df = construir_etiqueta(_df_ejemplo(), umbral=3.0)
    assert df[COLUMNA_ETIQUETA].tolist() == [0, 0, 0, 1]


def test_etiqueta_no_modifica_el_dataframe_original() -> None:
    original = _df_ejemplo()
    construir_etiqueta(original)
    assert COLUMNA_ETIQUETA not in original.columns


def test_etiqueta_sobre_dataframe_vacio() -> None:
    df = construir_etiqueta(pd.DataFrame({"CO(GT)": [], "T": []}))
    assert df.empty
    assert COLUMNA_ETIQUETA in df.columns
