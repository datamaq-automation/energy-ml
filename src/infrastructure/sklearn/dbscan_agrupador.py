"""src/infrastructure/sklearn/dbscan_agrupador.py — Agrupa eventos de carga por |ΔP| con DBSCAN."""

import numpy as np
from sklearn.cluster import DBSCAN

from src.domain.cargas.entities import EventoCarga


class DbscanAgrupador:
    """Implementa AgrupadorEventos: encendidos y apagados de la misma carga caen en el mismo grupo."""

    def __init__(self, eps_kw: float, min_eventos: int) -> None:
        self._modelo = DBSCAN(eps=eps_kw, min_samples=min_eventos)

    def agrupar(self, eventos: list[EventoCarga]) -> list[int]:
        magnitudes = np.array([[abs(e.delta_kw)] for e in eventos])
        return [int(e) for e in self._modelo.fit_predict(magnitudes)]
