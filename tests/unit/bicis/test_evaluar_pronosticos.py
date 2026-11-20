"""tests/unit/bicis/test_evaluar_pronosticos.py"""

from datetime import date, timedelta

import pytest

from src.application.bicis.dtos.pronostico import MuestraPronostico
from src.domain.bicis.modelos import VariablesPronostico
from src.infrastructure.bicis.evaluar_pronosticos import evaluar_2024_2025


def crear_muestra(fecha: date, viajes: int) -> MuestraPronostico:
    return MuestraPronostico(
        fecha_objetivo=fecha,
        variables=VariablesPronostico(
            dia_semana=fecha.weekday(),
            mes=fecha.month,
            viajes_dia_anterior=viajes - 1,
            viajes_semana_anterior=viajes - 2,
        ),
        viajes_reales=viajes,
    )


def test_evaluacion_usa_2024_para_entrenar_y_2025_para_probar() -> None:
    muestras = [
        crear_muestra(date(2024, 1, 1) + timedelta(days=dia), 100 + dia) for dia in range(20)
    ]
    muestras.extend(
        crear_muestra(date(2025, 1, 1) + timedelta(days=dia), 120 + dia) for dia in range(4)
    )

    resultado = evaluar_2024_2025(muestras)

    assert (resultado.dias_entrenamiento, resultado.dias_prueba) == (20, 4)
    assert resultado.linea_base.nombre == "Mismo día de la semana anterior"
    assert resultado.linea_base.mae == pytest.approx(2.0)
    assert resultado.linea_base.rmse == pytest.approx(2.0)
    assert resultado.bosque_aleatorio.mae >= 0
    assert resultado.bosque_aleatorio.rmse >= 0


def test_evaluacion_rechaza_períodos_incompletos() -> None:
    with pytest.raises(ValueError, match="2024 como de 2025"):
        evaluar_2024_2025([crear_muestra(date(2025, 1, 1), 10)])
