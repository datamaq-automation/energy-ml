"""tests/unit/ventas/test_reglas_ventas.py — Pruebas de las reglas puras del pronóstico de ventas."""

from __future__ import annotations

import pytest

from src.domain.ventas.modelos import (
    PISTAS,
    Pronosticos,
    calcular_mae,
    calcular_rmse,
    errores_por_grupo,
    errores_por_metodo,
    validar_sin_fuga,
)


def _pronosticos() -> Pronosticos:
    """Dos series: la (1, 1) en el grupo 0 y la (1, 2) en el grupo 1."""
    return Pronosticos(
        series=((1, 1), (1, 1), (1, 2), (1, 2)),
        fechas=("2017-01-01", "2017-01-02", "2017-01-01", "2017-01-02"),
        reales=(10.0, 20.0, 4.0, 6.0),
        por_metodo={"ayer": (12.0, 16.0, 4.0, 4.0), "lineal": (10.0, 20.0, 5.0, 5.0)},
    )


def test_mae_y_rmse_a_mano() -> None:
    """MAE promedia los errores; RMSE castiga más el error grande."""
    reales = (10.0, 10.0, 10.0, 10.0)
    predichos = (10.0, 10.0, 10.0, 14.0)
    assert calcular_mae(reales, predichos) == pytest.approx(1.0)
    assert calcular_rmse(reales, predichos) == pytest.approx(2.0)


def test_largos_distintos_o_vacios_fallan() -> None:
    with pytest.raises(ValueError):
        calcular_mae((1.0, 2.0), (1.0,))
    with pytest.raises(ValueError):
        calcular_rmse((), ())


def test_la_venta_del_dia_no_puede_ser_pista() -> None:
    """Usar 'sales' como pista sería fuga de datos: es justo lo que se quiere pronosticar."""
    validar_sin_fuga(PISTAS)
    with pytest.raises(ValueError, match="Fuga de datos"):
        validar_sin_fuga(["ayer", "sales"])


def test_errores_por_metodo() -> None:
    errores = {e.metodo: e for e in errores_por_metodo(_pronosticos())}
    assert errores["ayer"].mae == pytest.approx((2 + 4 + 0 + 2) / 4)
    assert errores["lineal"].mae == pytest.approx(0.5)
    assert errores["lineal"].rmse < errores["ayer"].rmse


def test_errores_por_grupo_separa_cada_serie() -> None:
    errores = errores_por_grupo(_pronosticos(), {(1, 1): 0, (1, 2): 1})
    por_clave = {(e.grupo, e.metodo): e for e in errores}
    assert len(errores) == 4
    assert por_clave[(0, "ayer")].mae == pytest.approx(3.0)
    assert por_clave[(0, "ayer")].venta_media == pytest.approx(15.0)
    assert por_clave[(0, "ayer")].error_relativo == pytest.approx(0.2)
    assert por_clave[(1, "lineal")].mae == pytest.approx(1.0)
