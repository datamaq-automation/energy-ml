"""tests/integration/test_arbol_clasificador.py — El árbol aprende a separar cargas por su salto."""

from datetime import datetime

from src.domain.cargas.entities import Salto
from src.infrastructure.sklearn.arbol_clasificador import ArbolClasificador

T0 = datetime(2026, 9, 20)


def salto(delta: float) -> Salto:
    return Salto(T0, delta, 0.0, 0.0)


def test_aprende_cargas_y_ruido_y_explica_sus_reglas() -> None:
    deltas = [90, -91, 89, -90, 40, -41, 39, -40, 1, -2, 0, 2]
    etiquetas = ["90 kW"] * 4 + ["40 kW"] * 4 + ["ninguna"] * 4
    arbol = ArbolClasificador()
    arbol.entrenar([salto(d) for d in deltas], etiquetas)
    assert arbol.predecir([salto(88), salto(-42), salto(-1)]) == ["90 kW", "40 kW", "ninguna"]
    assert "ΔP" in arbol.explicar()
    assert arbol.predecir([]) == []
