"""tests/unit/mantenimiento/test_graficos.py — Pruebas de los gráficos de mantenimiento."""

from pathlib import Path

from src.infrastructure.sklearn.mantenimiento_agrupamiento import KMetrics
from src.infrastructure.sklearn.mantenimiento_graficos import (
    save_confusion_matrix,
    save_k_charts,
)


def test_k_charts_are_saved(tmp_path: Path) -> None:
    metrics = [KMetrics(2, 100.0, 0.3), KMetrics(3, 80.0, 0.35)]
    target = tmp_path / "salida" / "codo_silueta.png"
    save_k_charts(metrics, target)
    assert target.stat().st_size > 0


def test_confusion_matrix_is_saved(tmp_path: Path) -> None:
    target = tmp_path / "matriz.png"
    save_confusion_matrix(tn=90, fp=5, fn=2, tp=3, threshold=0.24, path=target)
    assert target.stat().st_size > 0
