"""tests/unit/bicis/test_preparar_pronosticos.py"""

from datetime import date

import pytest

from src.application.bicis.use_cases.preparar_pronosticos import PrepararPronosticosUseCase
from src.domain.bicis.value_objects import DiaViajes, SerieDiariaViajes


class RepositorioEnMemoria:
    def __init__(self, serie: SerieDiariaViajes) -> None:
        self._serie = serie
        self.intervalo: tuple[date, date] | None = None

    def obtener(self, desde: date, hasta: date) -> SerieDiariaViajes:
        self.intervalo = desde, hasta
        return self._serie


def crear_serie(*dias: tuple[date, int]) -> SerieDiariaViajes:
    return SerieDiariaViajes(tuple(DiaViajes(fecha, viajes) for fecha, viajes in dias))


def test_prepara_muestras_y_reporta_fechas_excluidas() -> None:
    desde, hasta = date(2025, 1, 8), date(2025, 1, 10)
    repositorio = RepositorioEnMemoria(
        crear_serie(
            (date(2025, 1, 1), 7),
            (date(2025, 1, 7), 14),
            (date(2025, 1, 8), 100),
            (date(2025, 1, 10), 160),
        )
    )

    resultado = PrepararPronosticosUseCase(repositorio).execute(desde, hasta)

    assert repositorio.intervalo == (date(2025, 1, 1), hasta)
    assert len(resultado.muestras) == 1
    muestra = resultado.muestras[0]
    assert muestra.fecha_objetivo == date(2025, 1, 8)
    assert muestra.viajes_reales == 100
    assert muestra.variables.viajes_dia_anterior == 14
    assert muestra.variables.viajes_semana_anterior == 7
    assert resultado.dias_faltantes == (date(2025, 1, 9),)
    assert resultado.dias_sin_rezagos == (date(2025, 1, 10),)


def test_intervalo_invertido_se_rechaza_sin_consultar_repositorio() -> None:
    repositorio = RepositorioEnMemoria(crear_serie((date(2025, 1, 1), 7)))
    caso_de_uso = PrepararPronosticosUseCase(repositorio)

    with pytest.raises(ValueError, match="posterior"):
        caso_de_uso.execute(date(2025, 1, 2), date(2025, 1, 1))

    assert repositorio.intervalo is None
