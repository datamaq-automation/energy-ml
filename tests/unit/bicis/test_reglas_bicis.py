"""tests/unit/bicis/test_reglas_bicis.py"""

from datetime import date

import pytest

from src.domain.bicis.modelos import DiaViajes, SerieDiariaViajes
from src.domain.bicis.reglas import (
    construir_variables_pronostico,
    viajes_mismo_dia_semana_anterior,
)


def crear_serie(*dias: tuple[date, int]) -> SerieDiariaViajes:
    return SerieDiariaViajes(tuple(DiaViajes(fecha, viajes) for fecha, viajes in dias))


def test_dia_rechaza_cantidad_negativa() -> None:
    with pytest.raises(ValueError, match="no puede ser negativa"):
        DiaViajes(date(2025, 1, 1), -1)


@pytest.mark.parametrize(
    "dias, mensaje",
    [
        (((date(2025, 1, 1), 2), (date(2025, 1, 1), 3)), "duplicada"),
        (((date(2025, 1, 2), 2), (date(2025, 1, 1), 3)), "orden ascendente"),
    ],
)
def test_serie_rechaza_fechas_duplicadas_o_desordenadas(
    dias: tuple[tuple[date, int], ...], mensaje: str
) -> None:
    with pytest.raises(ValueError, match=mensaje):
        crear_serie(*dias)


def test_serie_informa_dias_faltantes_sin_completarlos() -> None:
    serie = crear_serie((date(2025, 1, 1), 10), (date(2025, 1, 3), 12))

    assert serie.dias_faltantes(date(2025, 1, 1), date(2025, 1, 4)) == (
        date(2025, 1, 2),
        date(2025, 1, 4),
    )
    assert len(serie.dias) == 2


def test_pronostico_usa_solo_calendario_e_observaciones_anteriores() -> None:
    fecha_objetivo = date(2025, 1, 8)
    serie = crear_serie(
        (date(2025, 1, 1), 7),
        (date(2025, 1, 7), 14),
        (fecha_objetivo, 100),
        (date(2025, 1, 9), 200),
    )
    solo_historial = crear_serie((date(2025, 1, 1), 7), (date(2025, 1, 7), 14))

    assert viajes_mismo_dia_semana_anterior(serie, fecha_objetivo) == 7
    variables = construir_variables_pronostico(serie, fecha_objetivo)
    assert variables == construir_variables_pronostico(solo_historial, fecha_objetivo)
    assert variables is not None
    assert (
        variables.dia_semana,
        variables.mes,
        variables.viajes_dia_anterior,
        variables.viajes_semana_anterior,
    ) == (2, 1, 14, 7)


def test_rezagos_no_disponibles_impiden_construir_variables() -> None:
    serie = crear_serie((date(2025, 1, 1), 7))

    assert construir_variables_pronostico(serie, date(2025, 1, 8)) is None
