"""tests/unit/crecidas/test_niveles_oficiales.py — Niveles oficiales de Tigre (Prefectura Naval)."""

import pytest

from src.domain.crecidas.modelos import (
    NIVELES_OFICIALES_TIGRE,
    Escenario,
    NivelesOficiales,
)
from src.domain.crecidas.reglas import clasificar_escenario


class TestNivelesOficialesTigre:
    def test_valores_oficiales(self) -> None:
        assert NIVELES_OFICIALES_TIGRE.alerta_m == pytest.approx(3.30)
        assert NIVELES_OFICIALES_TIGRE.evacuacion_m == pytest.approx(3.80)
        assert NIVELES_OFICIALES_TIGRE.aguas_bajas_m == pytest.approx(0.30)

    def test_alerta_menor_que_evacuacion(self) -> None:
        assert NIVELES_OFICIALES_TIGRE.alerta_m < NIVELES_OFICIALES_TIGRE.evacuacion_m


class TestAUmbrales:
    def test_alerta_y_evacuacion_se_mapean_a_alerta_y_crecida(self) -> None:
        umbrales = NIVELES_OFICIALES_TIGRE.a_umbrales(vigilancia_m=2.5)

        assert umbrales.vigilancia_m == pytest.approx(2.5)
        assert umbrales.alerta_m == pytest.approx(3.30)
        assert umbrales.crecida_m == pytest.approx(3.80)

    def test_vigilancia_la_aporta_quien_llama(self) -> None:
        # La vigilancia no es oficial: no se inventa, se pasa explícitamente.
        umbrales = NIVELES_OFICIALES_TIGRE.a_umbrales(vigilancia_m=2.0)
        assert umbrales.vigilancia_m == pytest.approx(2.0)

    def test_vigilancia_que_no_respeta_el_orden_falla(self) -> None:
        with pytest.raises(ValueError):
            NIVELES_OFICIALES_TIGRE.a_umbrales(vigilancia_m=3.5)

    @pytest.mark.parametrize(
        "nivel, esperado",
        [
            (3.29, Escenario.VIGILANCIA),
            (3.30, Escenario.ALERTA),  # límite inclusivo, valor oficial
            (3.79, Escenario.ALERTA),
            (3.80, Escenario.CRECIDA),  # límite inclusivo, evacuación
        ],
    )
    def test_clasificacion_con_niveles_oficiales(self, nivel: float, esperado: Escenario) -> None:
        umbrales = NIVELES_OFICIALES_TIGRE.a_umbrales(vigilancia_m=2.5)
        assert clasificar_escenario(nivel, umbrales) == esperado


class TestNivelesOficialesInmutables:
    def test_es_inmutable(self) -> None:
        niveles = NivelesOficiales(alerta_m=1.0, evacuacion_m=2.0, aguas_bajas_m=0.1)
        with pytest.raises(AttributeError):
            niveles.alerta_m = 9.0  # type: ignore[misc]
