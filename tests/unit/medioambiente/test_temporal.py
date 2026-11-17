"""tests/unit/medioambiente/test_temporal.py — Tarea C: split temporal y cambio de distribución."""

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
from src.medioambiente.supervised import predecir_particion
from src.medioambiente.temporal import (
    comparar_splits,
    detectar_cambio_distribucion,
    split_temporal,
)


def _datos_con_fecha(n: int = 100) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fecha": pd.date_range("2004-03-10", periods=n, freq="h"),
            "valor": np.linspace(0.0, 1.0, n),
            COLUMNA_ETIQUETA: [i % 2 for i in range(n)],
        }
    )


def test_split_temporal_tamanos_y_orden() -> None:
    train, test = split_temporal(_datos_con_fecha())
    assert len(train) == 80
    assert len(test) == 20
    assert train["fecha"].max() < test["fecha"].min()


def test_split_temporal_sin_fecha_lanza_error() -> None:
    with pytest.raises(ValueError, match="fecha"):
        split_temporal(pd.DataFrame({"valor": [1.0, 2.0]}))


def test_split_temporal_proporcion_invalida_lanza_error() -> None:
    with pytest.raises(ValueError, match="proporcion_train"):
        split_temporal(_datos_con_fecha(), proporcion_train=1.5)


def test_comparar_splits_une_tablas_con_columna_split() -> None:
    tabla_aleatorio = pd.DataFrame({"modelo": ["a", "b"], "f1": [0.1, 0.2]})
    tabla_temporal = pd.DataFrame({"modelo": ["a", "b"], "f1": [0.3, 0.4]})
    comparada = comparar_splits(tabla_aleatorio, tabla_temporal)
    assert len(comparada) == 4
    assert list(comparada["split"]) == ["aleatorio", "aleatorio", "temporal", "temporal"]


def _parte_estacion(estacion: str, n: int = 50) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    datos = {columna: rng.normal(0.0, 1.0, n) for columna in COLUMNAS_FEATURES}
    if estacion == "invierno":
        datos["T_t1"] = rng.normal(5.0, 1.0, n)
        datos["T_t2"] = rng.normal(5.0, 1.0, n)
    else:
        datos["T_t1"] = rng.normal(30.0, 1.0, n)
        datos["T_t2"] = rng.normal(30.0, 1.0, n)
    return pd.DataFrame(datos)


def test_detectar_cambio_marca_solo_las_features_desplazadas() -> None:
    invierno = _parte_estacion("invierno")
    verano = _parte_estacion("verano")

    resultado = detectar_cambio_distribucion(invierno, verano, umbral=0.5)

    por_feature = resultado.set_index("feature")
    assert bool(por_feature.loc["T_t1", "cambio"]) is True
    assert bool(por_feature.loc["RH_t1", "cambio"]) is False
    assert bool(por_feature.loc["mes", "cambio"]) is False
    assert por_feature.loc["T_t1", "desvio_estandarizado"] > 10


def test_detectar_cambio_con_umbral_grande_no_marca_nada() -> None:
    resultado = detectar_cambio_distribucion(
        _parte_estacion("invierno"), _parte_estacion("verano"), umbral=100.0
    )
    assert not resultado["cambio"].any()


@pytest.mark.skipif(
    not (DEFAULT_DATA_DIR / CSV_FILENAME).exists(),
    reason="Dataset local ausente: ejecutar download_dataset() primero.",
)
def test_tarea_b_vs_c_sobre_datos_reales() -> None:
    datos = construir_etiqueta(construir_features(load_air_quality()))

    train_aleatorio, test_aleatorio = split_aleatorio(datos)
    tabla_aleatorio, _ = predecir_particion(train_aleatorio, test_aleatorio)

    train_temporal, test_temporal = split_temporal(datos)
    tabla_temporal, predicciones_temporales = predecir_particion(train_temporal, test_temporal)

    comparada = comparar_splits(tabla_aleatorio, tabla_temporal)
    assert len(comparada) == 6
    assert set(comparada["modelo"]) == {"linea_base", "regresion_logistica", "arbol"}

    baseline = comparada[comparada["modelo"] == "linea_base"].set_index("split")
    assert baseline.loc["aleatorio", "recall"] == 0.0
    assert baseline.loc["temporal", "recall"] == 0.0
    assert baseline.loc["aleatorio", "accuracy"] == pytest.approx(
        1 - test_aleatorio["episodio"].mean()
    )
    assert baseline.loc["temporal", "accuracy"] == pytest.approx(
        1 - test_temporal["episodio"].mean()
    )

    # El test temporal es posterior al train
    assert train_temporal["fecha"].max() < test_temporal["fecha"].min()
    # Hay cambio de distribución invierno → primavera entre train y test temporal
    cambio = detectar_cambio_distribucion(train_temporal, test_temporal)
    assert cambio["cambio"].any()
    # Predicciones válidas
    for nombre, prediccion in predicciones_temporales.items():
        assert set(np.unique(prediccion)) <= {0, 1}, nombre
