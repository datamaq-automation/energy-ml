"""tests/educacion/test_fail_risk_conclusion.py — Conclusión final e integración (Issue #5)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from educacion.fail_risk import CONCLUSION, run_conclusion, run_task_b

RAIZ = Path(__file__).resolve().parents[2]
MODULO = RAIZ / "educacion" / "fail_risk.py"

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


def test_conclusion_numbers_match_live_models(capsys: pytest.CaptureFixture[str]) -> None:
    """Si un cambio de versión altera los modelos, este test obliga a actualizar la conclusión."""
    result = run_task_b()
    capsys.readouterr()
    text = " ".join(CONCLUSION)

    metrics = result["metrics"]
    logistic = metrics["logistic_regression"]
    forest = metrics["random_forest"]

    def en_coma(value: float) -> str:
        return f"{value:.2f}".replace(".", ",")

    assert en_coma(float(logistic["f1"])) in text
    assert en_coma(float(logistic["recall"])) in text
    assert en_coma(float(forest["recall"])) in text


def test_run_conclusion_prints_every_paragraph(capsys: pytest.CaptureFixture[str]) -> None:
    run_conclusion()
    out = capsys.readouterr().out
    assert "Conclusión — Issue #5" in out
    for paragraph in CONCLUSION:
        assert paragraph in out


def test_module_runs_all_tasks_in_order_end_to_end() -> None:
    """Ejecuta el módulo completo como lo haría un alumno: A, B, C y conclusión."""
    env = {**os.environ, "MPLBACKEND": "Agg", "PYTHONUTF8": "1"}
    process = subprocess.run(
        [sys.executable, str(MODULO)],
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
