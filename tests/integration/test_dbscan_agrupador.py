"""tests/integration/test_dbscan_agrupador.py — DBSCAN separa familias de saltos de potencia."""

from datetime import datetime

from src.domain.cargas.entities import EventoCarga
from src.infrastructure.sklearn.dbscan_agrupador import DbscanAgrupador

T0 = datetime(2026, 9, 20)


def test_separa_carga_grande_de_carga_mediana_y_ruido() -> None:
    deltas = [90, -91, 92, -89, 35, -34, 36, -35, 300]
    etiquetas = DbscanAgrupador(eps_kw=5, min_eventos=3).agrupar([EventoCarga(T0, d) for d in deltas])
    assert len(set(etiquetas[:4])) == 1
    assert len(set(etiquetas[4:8])) == 1
    assert etiquetas[0] != etiquetas[4]
    assert etiquetas[8] == -1
