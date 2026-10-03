"""tests/unit/cargas/test_simulacion.py — El tablero simulado es reproducible y su verdad es coherente."""

from datetime import datetime

from src.domain.cargas.entities import CargaSimulada
from src.domain.cargas.simulacion import MUESTRAS_POR_DIA, simular_tablero

T0 = datetime(2026, 9, 1)
CARGAS = [CargaSimulada(potencia_kw=90, ciclos_por_dia=10, duracion_min=30)]


def test_misma_semilla_mismos_datos() -> None:
    assert simular_tablero(CARGAS, 2, 1.0, 5, T0) == simular_tablero(CARGAS, 2, 1.0, 5, T0)
    assert simular_tablero(CARGAS, 2, 1.0, 5, T0) != simular_tablero(CARGAS, 2, 1.0, 6, T0)


def test_la_verdad_alterna_encendidos_y_apagados_y_coincide_con_los_saltos() -> None:
    mediciones, verdad = simular_tablero(CARGAS, 3, 0.0, 1, T0)
    assert len(mediciones) == 3 * MUESTRAS_POR_DIA
    assert verdad, "la carga tiene que prenderse alguna vez"
    signos = [e.delta_kw > 0 for e in verdad]
    assert all(a != b for a, b in zip(signos, signos[1:], strict=False))
    potencia = {m.instante: m.potencia_kw for m in mediciones}
    previo = {b.instante: a.potencia_kw for a, b in zip(mediciones, mediciones[1:], strict=False)}
    # Sin ruido, el salto medido es el de la carga más la variación lenta de la base (< 1 kW por muestra).
    assert all(abs(potencia[e.instante] - previo[e.instante] - e.delta_kw) < 1 for e in verdad)
