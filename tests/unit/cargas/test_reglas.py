"""tests/unit/cargas/test_reglas.py — Reglas conjuntivas: cobertura, predicción y serialización."""

import pytest

from src.domain.cargas.reglas import Condicion, ConjuntoReglas, Regla

GRANDE = Condicion("delta_kw", ">", 60.0)
CHICO = Condicion("delta_kw", "<=", 60.0)


def regla(*condiciones: Condicion, clase: str = "encendido", soporte: int = 5) -> Regla:
    return Regla("r1", list(condiciones), clase, soporte=soporte, confianza=0.9)


def test_regla_sin_condiciones_es_invalida() -> None:
    with pytest.raises(ValueError):
        Regla("r0", [], "encendido", soporte=0, confianza=0.0)


@pytest.mark.parametrize(
    ("condicion", "valor", "cubre"),
    [
        (GRANDE, 90.0, True),
        (GRANDE, 60.0, False),
        (CHICO, 60.0, True),
        (CHICO, 61.0, False),
        (Condicion("delta_kw", "==", 90.0), 90.0, True),
        (Condicion("delta_kw", "==", 90.0), 90.5, False),
    ],
)
def test_cubre_segun_operador(condicion: Condicion, valor: float, cubre: bool) -> None:
    assert regla(condicion).cubre({"delta_kw": valor}) is cubre


def test_no_cubre_si_falta_el_rasgo() -> None:
    assert not regla(GRANDE).cubre({"otro": 90.0})


def test_todas_las_condiciones_deben_cumplirse() -> None:
    r = regla(GRANDE, Condicion("delta_previo_kw", "<=", 5.0))
    assert r.cubre({"delta_kw": 90.0, "delta_previo_kw": 1.0})
    assert not r.cubre({"delta_kw": 90.0, "delta_previo_kw": 40.0})


def test_texto_legible() -> None:
    r = regla(GRANDE, Condicion("delta_previo_kw", "<=", 5.0))
    assert r.a_texto() == (
        "IF delta_kw > 60.00 AND delta_previo_kw <= 5.00 "
        "THEN encendido (soporte=5, confianza=90.00%)"
    )


def test_predice_con_la_primera_regla_que_cubre() -> None:
    conjunto = ConjuntoReglas(
        [regla(GRANDE, clase="encendido"), regla(CHICO, clase="ruido")], numero_ejemplos=10
    )
    assert conjunto.predecir({"delta_kw": 90.0}) == "encendido"
    assert conjunto.predecir({"delta_kw": 10.0}) == "ruido"
    assert conjunto.predecir({}) is None


def test_cobertura_total() -> None:
    conjunto = ConjuntoReglas([regla(GRANDE, soporte=3), regla(CHICO, soporte=5)], numero_ejemplos=10)
    assert conjunto.cobertura_total() == 0.8
    assert ConjuntoReglas([regla(GRANDE)], numero_ejemplos=0).cobertura_total() == 0.0
