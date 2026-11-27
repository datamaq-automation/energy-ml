"""tests/e2e/test_tarea_abc_runner.py — python -m src.infrastructure.cli.analizar_medioambiente: Tareas A, B y C en orden."""

from pathlib import Path

import pytest

from src.adapters.medioambiente.gateways.air_quality_uci_gateway import (
    CSV_FILENAME,
    DEFAULT_DATA_DIR,
)
from src.infrastructure.cli.analizar_medioambiente import ejecutar_tareas


@pytest.mark.skipif(
    not (DEFAULT_DATA_DIR / CSV_FILENAME).exists(),
    reason="Dataset local ausente: ejecutar download_dataset() primero.",
)
def test_ejecutar_tareas_devuelve_resultados_completos(tmp_path: Path) -> None:
    respuesta = ejecutar_tareas(destino_imagenes=tmp_path)
    assert respuesta.mejor_k in (2, 3, 4, 5, 6)
    assert len(respuesta.diagnosticos) == 5
    assert len(respuesta.metricas) == 6
    assert {m.split for m in respuesta.metricas} == {"aleatorio", "temporal"}
    assert {m.modelo for m in respuesta.metricas} == {
        "linea_base",
        "regresion_logistica",
        "arbol",
    }
    assert respuesta.mejor_modelo in {"regresion_logistica", "arbol"}
    assert len(respuesta.matriz_confusion) == 2
    assert sum(sum(fila) for fila in respuesta.matriz_confusion) > 0
    assert respuesta.features_con_cambio
    assert len(respuesta.eventos) == 3
    assert (tmp_path / "codo_kmeans.png").stat().st_size > 0
    assert (tmp_path / "silueta_kmeans.png").stat().st_size > 0
