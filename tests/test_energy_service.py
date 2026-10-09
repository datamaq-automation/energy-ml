import pytest

from src.domain.services.energy_service import calcular_consumo_activo


def test_calcular_consumo_activo():
    assert calcular_consumo_activo(100.0, 1.0) == 0.1


def test_consumo_de_potencia_alta():
    assert calcular_consumo_activo(1000.0, 1.0) == 1.0


def test_potencia_negativa_lanza_error():
    with pytest.raises(ValueError):
        calcular_consumo_activo(-5.0, 1.0)
