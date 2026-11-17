"""tests/unit/medioambiente/test_unsupervised.py — Tarea A: K-means, codo y silueta."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.medioambiente.data import CSV_FILENAME, DEFAULT_DATA_DIR, load_air_quality
from src.medioambiente.preprocess import construir_etiqueta
from src.medioambiente.unsupervised import (
    COLUMNAS_AGROUPAMIENTO,
    agrupar_meteo,
    calcular_diagnosticos_k,
    graficar_diagnosticos,
    mejor_k,
    proporcion_episodios,
    resumen_grupos,
)


def _datos_blobs(n_por_grupo: int = 30) -> pd.DataFrame:
    """Tres condiciones climáticas bien separadas: frío-húmedo, templado, cálido-secas."""
    rng = np.random.default_rng(42)
    frio = rng.normal(loc=[5.0, 90.0, 0.5], scale=0.5, size=(n_por_grupo, 3))
    templado = rng.normal(loc=[18.0, 55.0, 0.9], scale=0.5, size=(n_por_grupo, 3))
    calido = rng.normal(loc=[32.0, 30.0, 1.4], scale=0.5, size=(n_por_grupo, 3))
    datos = np.vstack([frio, templado, calido])
    return pd.DataFrame(datos, columns=COLUMNAS_AGROUPAMIENTO)


def test_diagnosticos_cubre_k_de_2_a_6() -> None:
    resultados = calcular_diagnosticos_k(_datos_blobs())
    assert list(resultados["k"]) == [2, 3, 4, 5, 6]
    assert resultados["inercia"].is_monotonic_decreasing
    assert resultados["silueta"].between(-1.0, 1.0).all()
    assert resultados["silueta"].notna().all()


def test_mejor_k_elige_la_mayor_silueta() -> None:
    resultados = pd.DataFrame(
        {
            "k": [2, 3, 4, 5, 6],
            "inercia": [100.0, 60.0, 45.0, 40.0, 38.0],
            "silueta": [0.45, 0.62, 0.51, 0.47, 0.40],
        }
    )
    assert mejor_k(resultados) == 3


def test_blobs_sepados_puntuan_mejor_k3_que_k2() -> None:
    resultados = calcular_diagnosticos_k(_datos_blobs()).set_index("k")
    assert resultados.loc[3, "silueta"] > resultados.loc[2, "silueta"]


def test_mejor_k_sin_resultados_lanza_error() -> None:
    with pytest.raises(ValueError, match="resultados"):
        mejor_k(pd.DataFrame(columns=["k", "inercia", "silueta"]))


def test_agrupar_agrega_columna_grupo_sin_tocar_los_datos() -> None:
    datos = _datos_blobs()
    agrupado = agrupar_meteo(datos, k=3)
    assert "grupo" in agrupado.columns
    assert len(agrupado) == len(datos)
    assert set(agrupado.columns) == set(datos.columns) | {"grupo"}
    assert set(agrupado["grupo"]) == {0, 1, 2}
    # Cada blob cae en un grupo distinto
    assert agrupado.groupby("grupo").size().tolist() == [30, 30, 30]


def test_agrupar_con_columnas_faltantes_lanza_error() -> None:
    with pytest.raises(ValueError, match="Faltan columnas"):
        agrupar_meteo(pd.DataFrame({"T": [1.0]}), k=2)


def test_resumen_grupos_promedia_meteo_por_grupo() -> None:
    df = pd.DataFrame(
        {
            "grupo": [0, 0, 1, 1],
            "T": [5.0, 7.0, 30.0, 32.0],
            "RH": [90.0, 80.0, 30.0, 40.0],
            "AH": [0.5, 0.6, 1.4, 1.5],
        }
    )
    resumen = resumen_grupos(df)
    assert resumen.loc[0, "T_mean"] == pytest.approx(6.0)
    assert resumen.loc[1, "T_mean"] == pytest.approx(31.0)
    assert resumen.loc[0, "T_size"] == 2


def test_resumen_grupos_sin_grupo_lanza_error() -> None:
    with pytest.raises(ValueError, match="grupo"):
        resumen_grupos(pd.DataFrame({"T": [1.0]}))


def test_proporcion_episodios_solo_sobre_filas_con_etiqueta() -> None:
    df = pd.DataFrame(
        {
            "grupo": [0, 0, 1, 1, 1],
            "episodio": [1, 0, 1, 1, np.nan],
        }
    )
    resumen = proporcion_episodios(df)
    assert resumen.loc[0, "n_horas"] == 2
    assert resumen.loc[0, "proporcion_episodio"] == pytest.approx(0.5)
    assert resumen.loc[1, "n_horas"] == 2  # la fila con episodio NaN no cuenta
    assert resumen.loc[1, "proporcion_episodio"] == pytest.approx(1.0)


def test_proporcion_episodios_sin_etiqueta_lanza_error() -> None:
    with pytest.raises(ValueError, match="episodio"):
        proporcion_episodios(pd.DataFrame({"grupo": [0, 1]}))


def test_graficos_de_codo_y_silueta_se_guardan(tmp_path: Path) -> None:
    resultados = pd.DataFrame(
        {"k": [2, 3, 4], "inercia": [120.0, 60.0, 45.0], "silueta": [0.55, 0.72, 0.48]}
    )
    ruta_codo, ruta_silueta = graficar_diagnosticos(resultados, tmp_path / "imagenes")
    assert ruta_codo == tmp_path / "imagenes" / "codo_kmeans.png"
    assert ruta_codo.stat().st_size > 0
    assert ruta_silueta.stat().st_size > 0
    assert ruta_silueta.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.skipif(
    not (DEFAULT_DATA_DIR / CSV_FILENAME).exists(),
    reason="Dataset local ausente: ejecutar download_dataset() primero.",
)
def test_tarea_a_sobre_datos_reales() -> None:
    datos = load_air_quality()
    resultados = calcular_diagnosticos_k(datos)
    k_elegido = mejor_k(resultados)
    assert 2 <= k_elegido <= 6

    agrupado = construir_etiqueta(agrupar_meteo(datos, k=k_elegido))
    resumen = resumen_grupos(agrupado)
    assert len(resumen) == k_elegido
    assert {"T_mean", "RH_mean", "AH_mean"} <= set(resumen.columns)

    proporcion = proporcion_episodios(agrupado)
    assert proporcion["n_horas"].sum() == len(agrupado)
    assert proporcion["proporcion_episodio"].between(0.0, 1.0).all()
