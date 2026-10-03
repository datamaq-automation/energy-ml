"""tests/unit/cargas/test_supervisado.py — Saltos con contexto, etiquetas y matriz de confusión."""

from datetime import datetime, timedelta

import pytest

from src.domain.cargas.entities import EventoReal, Medicion
from src.domain.cargas.supervisado import NINGUNA, armar_saltos, etiquetar, matriz_confusion

T0 = datetime(2026, 9, 1)


def t(i: int) -> datetime:
    return T0 + timedelta(minutes=5 * i)


def test_armar_saltos_agrega_el_salto_previo_y_el_siguiente() -> None:
    potencias = [100, 190, 191, 101]
    saltos = armar_saltos([Medicion(t(i), p) for i, p in reversed(list(enumerate(potencias)))])
    assert [s.instante for s in saltos] == [t(1), t(2), t(3)]
    assert [s.rasgos for s in saltos] == [[90, 0, 1], [1, 90, -90], [-90, 1, 0]]


def test_etiquetar_usa_la_verdad_y_la_carga_mas_grande_si_coinciden() -> None:
    saltos = armar_saltos([Medicion(t(i), p) for i, p in enumerate([100, 190, 191, 61])])
    verdad = [EventoReal(t(1), 90, 90), EventoReal(t(3), -90, 90), EventoReal(t(3), -40, 40)]
    assert etiquetar(saltos, verdad) == ["90 kW", NINGUNA, "90 kW"]


def test_matriz_confusion_calcula_exactitud_sensibilidad_y_precision() -> None:
    reales = ["15 kW", "15 kW", NINGUNA, NINGUNA, "90 kW"]
    predichas = ["15 kW", NINGUNA, NINGUNA, "15 kW", "90 kW"]
    m = matriz_confusion(reales, predichas)
    assert m.clases == [NINGUNA, "90 kW", "15 kW"]
    assert m.celdas["15 kW"] == {NINGUNA: 1, "90 kW": 0, "15 kW": 1}
    assert m.exactitud == 0.6
    assert m.sensibilidad("15 kW") == 0.5 and m.precision("15 kW") == 0.5
    assert m.sensibilidad("90 kW") == 1 and m.precision("90 kW") == 1


def test_matriz_confusion_exige_una_prediccion_por_ejemplo() -> None:
    with pytest.raises(ValueError):
        matriz_confusion([NINGUNA], [])
