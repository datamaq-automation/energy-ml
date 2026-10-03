"""src/domain/cargas/supervisado.py — Ejemplos etiquetados y métricas para el clasificador supervisado."""

from datetime import datetime
from itertools import pairwise

from src.domain.cargas.entities import EventoReal, MatrizConfusion, Medicion, Salto

NINGUNA = "ninguna"


def armar_saltos(mediciones: list[Medicion]) -> list[Salto]:
    """Un ejemplo por cada par de mediciones consecutivas, sin umbral: el modelo decide qué es evento."""
    ordenadas = sorted(mediciones, key=lambda m: m.instante)
    deltas = [(b.instante, b.potencia_kw - a.potencia_kw) for a, b in pairwise(ordenadas)]
    return [
        Salto(
            instante=instante,
            delta_kw=round(delta, 2),
            delta_previo_kw=round(deltas[i - 1][1], 2) if i > 0 else 0.0,
            delta_siguiente_kw=round(deltas[i + 1][1], 2) if i + 1 < len(deltas) else 0.0,
        )
        for i, (instante, delta) in enumerate(deltas)
    ]


def nombre_carga(carga_kw: float) -> str:
    return f"{carga_kw:g} kW"


def etiquetar(saltos: list[Salto], verdad: list[EventoReal]) -> list[str]:
    """La respuesta correcta de cada salto: la carga que cambió en ese instante, o "ninguna".

    Si en el mismo instante cambiaron dos cargas, se etiqueta con la más grande.
    """
    por_instante: dict[datetime, float] = {}
    for evento in verdad:
        if evento.carga_kw > por_instante.get(evento.instante, 0):
            por_instante[evento.instante] = evento.carga_kw
    return [
        nombre_carga(por_instante[s.instante]) if s.instante in por_instante else NINGUNA
        for s in saltos
    ]


def matriz_confusion(reales: list[str], predichas: list[str]) -> MatrizConfusion:
    """Cruza la respuesta correcta con la del modelo; "ninguna" va primero y las cargas de mayor a menor."""
    if len(reales) != len(predichas):
        raise ValueError("Cada ejemplo necesita una etiqueta real y una predicha.")
    cargas = sorted((set(reales) | set(predichas)) - {NINGUNA}, key=lambda c: -float(c.split()[0]))
    clases = [NINGUNA, *cargas]
    celdas = {r: dict.fromkeys(clases, 0) for r in clases}
    for real, predicha in zip(reales, predichas, strict=True):
        celdas[real][predicha] += 1
    return MatrizConfusion(clases=clases, celdas=celdas)
