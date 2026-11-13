"""tests/unit/medioambiente/test_features.py — Lags por reloj (t-1/t-2) y calendario."""

import pandas as pd
import pytest

from src.medioambiente.preprocess import (
    COLUMNAS_FEATURES,
    COLUMNAS_PROHIBIDAS,
    construir_features,
)


def _df_con_hueco() -> pd.DataFrame:
    """4 horas observadas con un hueco: falta la hora 21.00."""
    filas = [
        ("18/03/2004", "18.00.00", 10.0, 50.0, 0.70),
        ("18/03/2004", "19.00.00", 11.0, 51.0, 0.71),
        ("18/03/2004", "20.00.00", 12.0, 52.0, 0.72),
        ("18/03/2004", "22.00.00", 14.0, 54.0, 0.74),
    ]
    return pd.DataFrame(filas, columns=["Date", "Time", "T", "RH", "AH"])


def test_lags_se_calculan_por_reloj_no_por_posicion() -> None:
    df = construir_features(_df_con_hueco()).set_index("fecha")
    assert df.loc[pd.Timestamp("2004-03-18 19:00"), "T_t1"] == 10.0
    assert pd.isna(df.loc[pd.Timestamp("2004-03-18 19:00"), "T_t2"])
    # Hora 22: t-1 (21.00) no fue observada → NaN; t-2 (20.00) sí existió.
    assert pd.isna(df.loc[pd.Timestamp("2004-03-18 22:00"), "T_t1"])
    assert df.loc[pd.Timestamp("2004-03-18 22:00"), "T_t2"] == 12.0
    # Primera hora del dataset: sin lags.
    assert pd.isna(df.loc[pd.Timestamp("2004-03-18 18:00"), "T_t1"])
    assert pd.isna(df.loc[pd.Timestamp("2004-03-18 18:00"), "T_t2"])


def test_calendario_es_de_la_hora_a_predecir() -> None:
    df = construir_features(_df_con_hueco())
    fila = df.loc[df["Time"] == "19.00.00"].iloc[0]
    assert fila["hora"] == 19
    assert fila["dia_semana"] == pd.Timestamp("2004-03-18").dayofweek
    assert fila["mes"] == 3


def test_features_ordenadas_por_fecha() -> None:
    desordenado = _df_con_hueco().iloc[::-1].reset_index(drop=True)
    df = construir_features(desordenado)
    assert df["fecha"].is_monotonic_increasing
    assert list(df["Time"]) == ["18.00.00", "19.00.00", "20.00.00", "22.00.00"]


def test_features_no_incluyen_variables_prohibidas() -> None:
    df = construir_features(_df_con_hueco())
    x = df[COLUMNAS_FEATURES]
    assert list(x.columns) == list(COLUMNAS_FEATURES)
    assert not set(x.columns) & set(COLUMNAS_PROHIBIDAS)
    assert "fecha" not in x.columns


def test_features_lanza_error_si_faltan_columnas() -> None:
    with pytest.raises(ValueError, match="Faltan columnas"):
        construir_features(pd.DataFrame({"Date": ["01/01/2004"], "Time": ["10.00.00"]}))


def test_features_dataframe_vacio() -> None:
    vacio = pd.DataFrame(columns=["Date", "Time", "T", "RH", "AH"])
    df = construir_features(vacio)
    assert df.empty
    assert set(COLUMNAS_FEATURES) <= set(df.columns)
