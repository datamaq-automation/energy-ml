"""tests/unit/medioambiente/test_split.py — Split estratificado y transformación solo en train."""

import numpy as np
import pandas as pd
import pytest

from src.medioambiente.data import CSV_FILENAME, DEFAULT_DATA_DIR, load_air_quality
from src.medioambiente.preprocess import (
    COLUMNAS_FEATURES,
    COLUMNAS_PROHIBIDAS,
    construir_etiqueta,
    construir_features,
    crear_transformador,
)
from src.medioambiente.split import split_aleatorio


def _dataset(n: int = 100) -> pd.DataFrame:
    episodio = np.array([1 if i % 3 == 0 else 0 for i in range(n)], dtype="int8")
    return pd.DataFrame(
        {
            "fecha": pd.date_range("2004-03-10", periods=n, freq="h"),
            "valor": np.linspace(0.0, 1.0, n),
            "episodio": episodio,
        }
    )


def test_split_proporcion_estratificada_y_tamanos() -> None:
    dataset = _dataset()
    train, test = split_aleatorio(dataset)
    assert len(train) == 80
    assert len(test) == 20
    assert train["episodio"].mean() == pytest.approx(dataset["episodio"].mean(), abs=0.05)
    assert test["episodio"].mean() == pytest.approx(dataset["episodio"].mean(), abs=0.05)


def test_split_train_y_test_disjuntos() -> None:
    train, test = split_aleatorio(_dataset())
    assert set(train["fecha"]).isdisjoint(set(test["fecha"]))


def test_split_reproducible_con_misma_semilla() -> None:
    train1, test1 = split_aleatorio(_dataset())
    train2, test2 = split_aleatorio(_dataset())
    assert list(train1["fecha"]) == list(train2["fecha"])
    assert list(test1["fecha"]) == list(test2["fecha"])


def test_split_sin_etiqueta_lanza_error() -> None:
    with pytest.raises(ValueError, match="episodio"):
        split_aleatorio(pd.DataFrame({"fecha": [1, 2, 3]}))


def test_transformador_se_ajusta_solo_sobre_train() -> None:
    dataset = _dataset()
    dataset.loc[dataset.index[:40], "valor"] = np.nan  # faltantes solo al inicio
    train, test = split_aleatorio(dataset)
    x_train = train[["valor"]]
    x_test = test[["valor"]].copy()
    x_test.iloc[:, 0] = 1_000_000.0  # valor extremo solo en test

    pipeline = crear_transformador().fit(x_train)

    mediana_train = x_train.median()
    estadisticos_imputer = pd.Series(pipeline.named_steps["imputar"].statistics_, index=["valor"])
    assert np.allclose(estadisticos_imputer.to_numpy(), mediana_train.to_numpy())
    imputado = x_train.fillna(mediana_train)
    media_escalador = pipeline.named_steps["escalar"].mean_[0]
    assert media_escalador == pytest.approx(imputado["valor"].mean())
    assert media_escalador < 1000  # el extremo de test no contaminó la escala
    assert np.isfinite(pipeline.transform(x_test)).all()


def test_transformador_convierte_nan_a_valores_finitos() -> None:
    x_train = pd.DataFrame({"valor": [1.0, np.nan, 3.0, 5.0]})
    x_test = pd.DataFrame({"valor": [np.nan, 7.0]})
    pipeline = crear_transformador().fit(x_train)
    transformado = pipeline.transform(x_test)
    assert np.isfinite(transformado).all()


@pytest.mark.skipif(
    not (DEFAULT_DATA_DIR / CSV_FILENAME).exists(),
    reason="Dataset local ausente: ejecutar download_dataset() primero.",
)
def test_flujo_real_sin_fuga_en_x_train_y_x_test() -> None:
    datos = construir_etiqueta(construir_features(load_air_quality()))
    train, test = split_aleatorio(datos)
    for particion in (train, test):
        x = particion[COLUMNAS_FEATURES]
        y = particion["episodio"]
        assert not set(x.columns) & set(COLUMNAS_PROHIBIDAS)
        assert "CO(GT)" not in x.columns
        assert not (x.select_dtypes("number") == -200).any().any()
        assert y.isin([0, 1]).all()
    assert len(train) + len(test) == len(datos)
