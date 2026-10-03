"""tests/unit/cargas/test_evaluacion.py — Sensibilidad, precisión y cargas inventadas."""

from datetime import datetime, timedelta

from src.domain.cargas.entities import EventoDetectado, EventoReal
from src.domain.cargas.evaluacion import evaluar

T0 = datetime(2026, 9, 1)


def t(i: int) -> datetime:
    return T0 + timedelta(minutes=5 * i)


def test_evaluar_cuenta_detectados_bien_asignados_falsos_e_inventadas() -> None:
    verdad = [EventoReal(t(1), 90, 90), EventoReal(t(3), -90, 90), EventoReal(t(5), 40, 40), EventoReal(t(7), -40, 40)]
    detectados = [
        EventoDetectado(t(1), 91, 89.0),  # bien asignado
        EventoDetectado(t(3), -88, 89.0),  # bien asignado
        EventoDetectado(t(5), 41, None),  # detectado pero sin grupo
        EventoDetectado(t(9), 55, 55.0),  # no pasó nada: falso positivo, y 55 kW es inventada
    ]
    ev = evaluar(detectados, verdad)
    noventa, cuarenta = ev.por_carga
    assert (noventa.eventos_reales, noventa.detectados, noventa.bien_asignados) == (2, 2, 2)
    assert noventa.sensibilidad == 1 and noventa.potencia_estimada_kw == 89.0
    assert (cuarenta.detectados, cuarenta.bien_asignados, cuarenta.potencia_estimada_kw) == (1, 0, None)
    assert ev.falsos_positivos == 1 and ev.precision == 0.75
    assert ev.cargas_inventadas == [55.0]
