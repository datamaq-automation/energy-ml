"""tests/unit/ventas/test_pipeline_ventas.py — Pruebas de las Tareas A, B y C de ventas con datos sintéticos."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.adapters.ventas.controlador import ControladorVentas
from src.application.ventas.use_cases import AgruparSeriesUseCase, PronosticarDemandaUseCase
from src.infrastructure.cli.analizar_ventas import main as cli_main
from src.infrastructure.csv.venta_repository import CsvVentaRepository
from src.infrastructure.sklearn.ventas_agrupador import KMeansAgrupadorVentas, armar_fichas
from src.infrastructure.sklearn.ventas_pronosticador import (
    SklearnPronosticadorVentas,
    agregar_pistas,
)


def _crear_csv(ruta: Path) -> Path:
    """3 tiendas x 4 productos, 2016-2017, con niveles de venta distintos y patrón semanal."""
    rng = np.random.default_rng(42)
    fechas = pd.date_range("2016-01-01", "2017-03-31", freq="D")
    filas = []
    for tienda in (1, 2, 3):
        for producto in (1, 2, 3, 4):
            nivel = 10 * producto
            semanal = 1 + 0.3 * (fechas.day_of_week / 6)
            ventas = rng.poisson(nivel * semanal)
            filas.append(
                pd.DataFrame({"date": fechas, "store": tienda, "item": producto, "sales": ventas})
            )
    datos = pd.concat(filas)
    datos["date"] = datos["date"].dt.strftime("%Y-%m-%d")
    datos.to_csv(ruta, index=False)
    return ruta


def _controlador(csv: Path) -> ControladorVentas:
    fuente = CsvVentaRepository(csv)
    return ControladorVentas(
        AgruparSeriesUseCase(fuente, KMeansAgrupadorVentas()),
        PronosticarDemandaUseCase(fuente, SklearnPronosticadorVentas(arboles=20)),
    )


def test_csv_sin_columnas_falla(tmp_path: Path) -> None:
    ruta = tmp_path / "malo.csv"
    pd.DataFrame({"date": ["2017-01-01"], "sales": [1]}).to_csv(ruta, index=False)
    with pytest.raises(ValueError, match="faltan las columnas"):
        CsvVentaRepository(ruta).leer()


def test_fichas_y_pistas_sin_fuga(tmp_path: Path) -> None:
    """Las pistas 'ayer' y 'semana_pasada' miran solo días anteriores de la misma serie."""
    ventas = CsvVentaRepository(_crear_csv(tmp_path / "v.csv")).leer()
    fichas = armar_fichas(ventas)
    assert len(fichas) == 12
    assert list(fichas.columns) == ["mean", "std", "lun", "mar", "mie", "jue", "vie", "sab", "dom"]

    con_pistas = agregar_pistas(ventas)
    serie = con_pistas[(con_pistas["store"] == 2) & (con_pistas["item"] == 3)]
    assert pd.isna(serie["ayer"].iloc[0])
    assert serie["ayer"].iloc[5] == serie["sales"].iloc[4]
    assert serie["semana_pasada"].iloc[10] == serie["sales"].iloc[3]


def test_k_fuera_de_rango_falla(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no está entre"):
        _controlador(_crear_csv(tmp_path / "v.csv")).analizar(k_elegido=9)


def test_tareas_a_b_c(tmp_path: Path) -> None:
    """A: grupos para todas las series; B: el examen es solo 2017; C: error por grupo."""
    reporte = _controlador(_crear_csv(tmp_path / "v.csv")).analizar(k_elegido=2)

    agrupamiento = reporte.agrupamiento
    assert [m.k for m in agrupamiento.metricas] == [2, 3, 4, 5, 6]
    assert sum(p.cantidad_series for p in agrupamiento.perfiles) == 12
    assert len(agrupamiento.grupo_por_serie) == 12

    pronostico = reporte.pronostico
    assert min(pronostico.pronosticos.fechas) == "2017-01-01"
    assert len(pronostico.pronosticos.reales) == 12 * 90
    errores = {e.metodo: e.mae for e in pronostico.por_metodo}
    assert set(errores) == {"ayer", "lineal", "bosque"}
    assert errores["lineal"] < errores["ayer"]
    assert len(pronostico.por_grupo) == 2 * 3
    assert any("Bosque aleatorio" in r for r in reporte.renglones)


def test_cli_guarda_graficos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv = _crear_csv(tmp_path / "v.csv")
    salida = tmp_path / "salida"
    monkeypatch.setattr(
        "sys.argv",
        [
            "analizar_ventas.py",
            "--csv",
            str(csv),
            "--output-dir",
            str(salida),
            "--k",
            "2",
            "--arboles",
            "10",
        ],
    )
    cli_main()
    assert (salida / "ventas_codo_silueta.png").stat().st_size > 0
    assert (salida / "ventas_real_vs_pronostico.png").stat().st_size > 0


def test_cli_sin_dataset_no_rompe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["analizar_ventas.py", "--csv", str(tmp_path / "no.csv")])
    cli_main()
