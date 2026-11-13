"""tests/unit/crecidas/test_reglas_crecidas.py"""

import pytest

from src.domain.crecidas.modelos import Escenario, Umbrales
from src.domain.crecidas.reglas import clasificar_escenario, generar_alerta

UMBRALES = Umbrales(vigilancia_m=2.0, alerta_m=3.0, crecida_m=3.8)


class TestUmbrales:
    def test_orden_valido_se_acepta(self) -> None:
        assert Umbrales(1.0, 2.0, 3.0).alerta_m == 2.0

    @pytest.mark.parametrize(
        "vig, ale, cre",
        [(3.0, 2.0, 4.0), (1.0, 3.0, 2.5), (1.0, 2.0, 2.0)],
    )
    def test_orden_invalido_lanza_error(self, vig: float, ale: float, cre: float) -> None:
        with pytest.raises(ValueError):
            Umbrales(vig, ale, cre)


class TestClasificarEscenario:
    @pytest.mark.parametrize(
        "nivel, esperado",
        [
            (1.5, Escenario.NORMAL),
            (2.0, Escenario.VIGILANCIA),  # límite inclusivo
            (2.9, Escenario.VIGILANCIA),
            (3.0, Escenario.ALERTA),  # límite inclusivo
            (3.7, Escenario.ALERTA),
            (3.8, Escenario.CRECIDA),  # límite inclusivo
            (5.0, Escenario.CRECIDA),
            (-0.3, Escenario.NORMAL),
        ],
    )
    def test_clasifica_por_umbral(self, nivel: float, esperado: Escenario) -> None:
        assert clasificar_escenario(nivel, UMBRALES) == esperado


class TestGenerarAlerta:
    def test_normal_no_genera_alerta(self) -> None:
        assert generar_alerta(1.0, 6, UMBRALES) is None

    def test_vigilancia_no_genera_alerta(self) -> None:
        assert generar_alerta(2.5, 6, UMBRALES) is None

    def test_alerta_genera_registro_auditable(self) -> None:
        alerta = generar_alerta(3.2, 6, UMBRALES)
        assert alerta is not None
        assert alerta.escenario == Escenario.ALERTA
        assert alerta.nivel_previsto_m == 3.2
        assert alerta.horizonte_horas == 6
        assert alerta.umbral_disparado_m == 3.0

    def test_crecida_usa_umbral_de_crecida(self) -> None:
        alerta = generar_alerta(4.0, 6, UMBRALES)
        assert alerta is not None
        assert alerta.escenario == Escenario.CRECIDA
        assert alerta.umbral_disparado_m == 3.8

    def test_horizonte_no_positivo_lanza_error(self) -> None:
        with pytest.raises(ValueError):
            generar_alerta(4.0, 0, UMBRALES)
