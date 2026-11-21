"""tests/educacion/test_fail_risk_conclusion.py — Conclusión final e integración (Issue #5)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from src.adapters.educacion.controllers.tareas import ejecutar_tareas
from src.adapters.educacion.gateways.estudiantes_csv import EstudiantesCsv
from src.application.educacion.tareas import run_conclusion, run_task_b
from src.domain.educacion.modelos import CONCLUSION
from src.infrastructure.graficos.educacion import MatplotlibGraficador
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.educacion_agrupador import KMeansAgrupadorEstudiantes
from src.infrastructure.sklearn.educacion_modelos import SklearnEntrenadorRiesgo

RAIZ = Path(__file__).resolve().parents[2]

#: Fragmentos que la conclusión debe citar de la corrida real (semilla 42).
RESULTADOS_ESPERADOS = ("0,79", "0,73", "0,81", "23,6", "71,4", "0,65", "0,89")


def test_conclusion_is_a_single_page_in_spanish() -> None:
    assert 3 <= len(CONCLUSION) <= 5
    text = " ".join(CONCLUSION)
    assert 2000 <= len(text) <= 6000, "debe ser más o menos una página"
    assert all(paragraph.strip() for paragraph in CONCLUSION)
    for fragment in ("Qué se puede predecir", "límites", "estudiante"):
        assert fragment in text


def test_conclusion_covers_the_three_required_sections() -> None:
    text = " ".join(CONCLUSION)
    assert "Qué se puede predecir" in text
    assert "Con qué límites" in text
    assert "Cómo usar el resultado sin perjudicar al estudiante" in text


def test_conclusion_cites_real_results() -> None:
    text = " ".join(CONCLUSION)
    for fragment in RESULTADOS_ESPERADOS:
        assert fragment in text, f"falta el resultado {fragment} en la conclusión"


def test_conclusion_never_recommends_sanctioning() -> None:
    """La conclusión debe recomendar acompañar y prohibir sancionar/excluir."""
    text = " ".join(CONCLUSION)
    assert "NO debe usarse para decisiones administrativas" in text
    assert "no una sentencia" in text
    assert "datos identificables" in text
    assert "acompaña la decisión" in text or "acompañar" in text


def test_conclusion_numbers_match_live_models(caplog: pytest.LogCaptureFixture) -> None:
    """Si un cambio de versión altera los modelos, este test obliga a actualizar la conclusión."""
    with caplog.at_level("INFO", logger="backend-api"):
        result = run_task_b(EstudiantesCsv(), SklearnEntrenadorRiesgo(), logger)
    text = " ".join(CONCLUSION)

    metrics = result["metrics"]
    logistic = metrics["logistic_regression"]
    forest = metrics["random_forest"]

    def en_coma(value: float) -> str:
        return f"{value:.2f}".replace(".", ",")

    assert en_coma(float(logistic["f1"])) in text
    assert en_coma(float(logistic["recall"])) in text
    assert en_coma(float(forest["recall"])) in text


def test_run_conclusion_prints_every_paragraph(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("INFO", logger="backend-api"):
        run_conclusion(logger)
    out = caplog.text
    assert "Conclusión — Issue #5" in out
    for paragraph in CONCLUSION:
        assert paragraph in out


def test_controlador_ejecuta_las_cuatro_partes_en_orden(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Integración: el controlador de adapters corre A, B, C y la conclusión en orden."""
    monkeypatch.setattr(plt, "show", lambda: None)

    with caplog.at_level("INFO", logger="backend-api"):
        resultados = ejecutar_tareas(
            fuente=EstudiantesCsv(),
            agrupador=KMeansAgrupadorEstudiantes(),
            entrenador=SklearnEntrenadorRiesgo(),
            graficador=MatplotlibGraficador(),
            bitacora=logger,
        )

    assert set(resultados) == {"tarea_a", "tarea_b", "tarea_c", "conclusion"}
    out = caplog.text
    markers = ["Tarea A", "Tarea B", "Tarea C", "Conclusión — Issue #5"]
    positions = [out.index(marker) for marker in markers]
    assert positions == sorted(positions), "las tareas deben salir en orden"


def test_module_runs_all_tasks_in_order_end_to_end() -> None:
    """Ejecuta el módulo completo como lo haría un alumno: A, B, C y conclusión."""
    env = {**os.environ, "MPLBACKEND": "Agg", "PYTHONUTF8": "1"}
    process = subprocess.run(
        [sys.executable, "-m", "educacion.fail_risk"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(RAIZ),
        timeout=180,
        check=False,
    )
    assert process.returncode == 0, process.stderr[-2000:]
    assert "Traceback" not in process.stderr

    out = process.stdout
    markers = ["Tarea A", "Tarea B", "Tarea C", "Conclusión — Issue #5"]
    positions = [out.index(marker) for marker in markers]
    assert positions == sorted(positions), "las tareas deben salir en orden"
    assert "k elegido" in out
    assert "línea base" in out
    assert "por 'sex'" in out
    assert "Recomendación de uso" in out
    assert "NO debe usarse para decisiones administrativas" in out
