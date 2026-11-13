"""tests/unit/medioambiente/test_supervised.py — Tarea B: baseline, logística y árbol con CV."""

import numpy as np
import pandas as pd
import pytest

from src.medioambiente.data import CSV_FILENAME, DEFAULT_DATA_DIR, load_air_quality
from src.medioambiente.preprocess import (
    COLUMNA_ETIQUETA,
    COLUMNAS_FEATURES,
    construir_etiqueta,
    construir_features,
)
from src.medioambiente.split import split_aleatorio
from src.medioambiente.supervised import (
    ajustar_transformacion,
    entrenar_modelos,
    linea_base,
    matriz_confusion,
    metricas_episodio,
    predecir_particion,
    separar_xy,
)


def _particion(n: int, semilla: int, forzar_etiqueta: list[int] | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(semilla)
    datos = {columna: rng.normal(0.0, 1.0, n) for columna in COLUMNAS_FEATURES}
    particion = pd.DataFrame(datos)
    etiqueta = (
        forzar_etiqueta
        if forzar_etiqueta is not None
        else list(rng.integers(0, 2, n, dtype="int8"))
    )
    particion[COLUMNA_ETIQUETA] = etiqueta
    return particion


def test_metricas_episodio_valores_conocidos() -> None:
    y_verdadero = pd.Series([1, 1, 0, 0])
    y_predicho = np.array([1, 0, 1, 0])
    metricas = metricas_episodio(y_verdadero, y_predicho)
    assert metricas["accuracy"] == pytest.approx(0.5)
    assert metricas["precision"] == pytest.approx(0.5)
    assert metricas["recall"] == pytest.approx(0.5)
    assert metricas["f1"] == pytest.approx(0.5)


def test_linea_base_siempre_predice_sin_episodio() -> None:
    y_verdadero = pd.Series([0, 0, 0, 1, 1])
    metricas = linea_base(y_verdadero)
    assert metricas["accuracy"] == pytest.approx(0.6)
    assert metricas["recall"] == 0.0
    assert metricas["precision"] == 0.0
    assert metricas["f1"] == 0.0


def test_matriz_confusion_orden_tn_fp_fn_tp() -> None:
    y_verdadero = pd.Series([1, 1, 0, 0, 1])
    y_predicho = np.array([1, 0, 0, 0, 1])
    matriz = matriz_confusion(y_verdadero, y_predicho)
    assert matriz.shape == (2, 2)
    assert matriz.tolist() == [[2, 0], [1, 2]]


def test_separar_xy_sin_etiqueta_lanza_error() -> None:
    with pytest.raises(ValueError, match="Faltan columnas"):
        separar_xy(pd.DataFrame({"T_t1": [1.0]}))


def test_transformacion_se_ajusta_solo_en_train() -> None:
    train = _particion(80, semilla=1)
    test = _particion(30, semilla=2, forzar_etiqueta=[0, 1] * 15)
    idx_t = COLUMNAS_FEATURES.index("T_t1")
    test["T_t1"] = 1_000_000.0  # valor extremo solo en test
    train.loc[train.index[:20], "T_t1"] = np.nan  # faltantes solo en train

    x_train_t, x_test_t = ajustar_transformacion(train, test)

    assert np.isfinite(x_train_t).all()
    assert x_train_t[:, idx_t].mean() == pytest.approx(0.0, abs=0.3)  # media de train
    assert x_test_t[:, idx_t].mean() > 100_000  # el extremo de test no reescaló nada


def test_entrenar_modelos_con_cv_de_profundidad() -> None:
    train = _particion(120, semilla=1)
    test = _particion(40, semilla=2, forzar_etiqueta=[0, 1] * 20)
    x_train_t, x_test_t = ajustar_transformacion(train, test)
    _, y_train = separar_xy(train)

    modelos = entrenar_modelos(x_train_t, y_train)

    assert set(modelos) == {"regresion_logistica", "arbol"}
    assert modelos["regresion_logistica"].class_weight == "balanced"
    assert modelos["arbol"].best_params_["max_depth"] in [3, 4, 5, 6]
    assert set(np.unique(modelos["arbol"].predict(x_test_t))) <= {0, 1}


def test_predecir_particion_devuelve_tabla_y_predicciones() -> None:
    train = _particion(150, semilla=1)
    test = _particion(60, semilla=2, forzar_etiqueta=[0, 1] * 30)

    tabla, predicciones = predecir_particion(train, test)

    assert list(tabla["modelo"]) == ["linea_base", "regresion_logistica", "arbol"]
    assert set(predicciones) == {"linea_base", "regresion_logistica", "arbol"}
    for columna in ("accuracy", "precision", "recall", "f1"):
        assert tabla[columna].between(0.0, 1.0).all()
    assert len(predicciones["arbol"]) == len(test)
    assert tabla.loc[tabla["modelo"] == "linea_base", "f1"].iloc[0] == 0.0


@pytest.mark.skipif(
    not (DEFAULT_DATA_DIR / CSV_FILENAME).exists(),
    reason="Dataset local ausente: ejecutar download_dataset() primero.",
)
def test_tarea_b_sobre_datos_reales() -> None:
    datos = construir_etiqueta(construir_features(load_air_quality()))
    train, test = split_aleatorio(datos)
    tabla, predicciones = predecir_particion(train, test)

    assert len(tabla) == 3
    baseline = tabla.loc[tabla["modelo"] == "linea_base"].iloc[0]
    assert baseline["accuracy"] == pytest.approx(1 - test["episodio"].mean())
    assert baseline["recall"] == 0.0
    for nombre, prediccion in predicciones.items():
        assert set(np.unique(prediccion)) <= {0, 1}, nombre
        assert len(prediccion) == len(test), nombre
