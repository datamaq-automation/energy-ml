"""tests/e2e/test_tarea_abc_runner.py — python -m src.medioambiente: Tareas A, B y C en orden."""

from pathlib import Path

import pytest

from src.medioambiente.__main__ import ejecutar_tareas
from src.medioambiente.data import CSV_FILENAME, DEFAULT_DATA_DIR


@pytest.mark.skipif(
    not (DEFAULT_DATA_DIR / CSV_FILENAME).exists(),
    reason="Dataset local ausente: ejecutar download_dataset() primero.",
)
def test_ejecutar_tareas_devuelve_resultados_completos(tmp_path: Path) -> None:
    resultados = ejecutar_tareas(destino_imagenes=tmp_path)

    assert resultados["mejor_k"] in (2, 3, 4, 5, 6)
    assert len(resultados["diagnosticos"]) == 5
    assert len(resultados["tabla_comparada"]) == 6
    assert set(resultados["tabla_comparada"]["split"]) == {"aleatorio", "temporal"}
    assert set(resultados["tabla_comparada"]["modelo"]) == {
        "linea_base",
        "regresion_logistica",
        "arbol",
    }
    assert resultados["mejor_modelo"] in {"regresion_logistica", "arbol"}
    assert resultados["matriz_confusion"].shape == (2, 2)
    assert resultados["matriz_confusion"].sum() > 0
    assert resultados["cambio_distribucion"]["cambio"].any()
    assert (tmp_path / "codo_kmeans.png").stat().st_size > 0
    assert (tmp_path / "silueta_kmeans.png").stat().st_size > 0
