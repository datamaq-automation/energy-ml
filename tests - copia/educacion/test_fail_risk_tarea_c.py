"""tests/educacion/test_fail_risk_tarea_c.py — Cobertura total de la Tarea C (Issue #5)."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from educacion.fail_risk import (
    FAIRNESS_GAP_THRESHOLD,
    MIN_SUBGROUP_N,
    MODEL_FEATURES,
    RECOMMENDATION,
    SUBGROUP_COLUMNS,
    analyze_fairness,
    evaluate_predictions,
    fit_real_models,
    load_students,
    pick_best_model,
    run_task_c,
    split_train_test,
    subgroup_metrics,
)


@pytest.fixture(scope="module")
def students() -> pd.DataFrame:
    """Dataset real una sola vez para toda la suite de la Tarea C."""
    return load_students()


@pytest.fixture(scope="module")
def task_c(students: pd.DataFrame) -> SimpleNamespace:
    """Misma corrida que run_task_c, pero expuesta para testear piezas individuales."""
    x_train, x_test, y_train, y_test = split_train_test(students)
    models = fit_real_models(x_train, y_train)
    metrics = {
        name: evaluate_predictions(y_test, model.predict(x_test)) for name, model in models.items()
    }
    best = pick_best_model(metrics)
    predictions = models[best].predict(x_test)
    fairness = {
        column: subgroup_metrics(y_test, predictions, x_test[column]) for column in SUBGROUP_COLUMNS
    }
    return SimpleNamespace(
        x_test=x_test,
        y_test=y_test,
        models=models,
        metrics=metrics,
        best=best,
        predictions=predictions,
        fairness=fairness,
    )


# ------------------------------------------------------------------------------
# Métricas por subgrupo (solo agregados)
# ------------------------------------------------------------------------------


def test_subgroup_columns_match_issue(task_c: SimpleNamespace) -> None:
    assert SUBGROUP_COLUMNS == ("sex", "school")
    assert set(task_c.fairness) == {"sex", "school"}


def test_subgroup_metrics_covers_every_group(task_c: SimpleNamespace) -> None:
    expected = {"sex": {"F", "M"}, "school": {"GP", "MS"}}
    for column, table in task_c.fairness.items():
        assert set(table["group"]) == expected[column]
        assert len(table) == 2
        assert set(table.columns) == {"group", "n", "n_desaprobados", "precision", "recall"}


def test_subgroup_metrics_counts_are_consistent(task_c: SimpleNamespace) -> None:
    for table in task_c.fairness.values():
        assert int(table["n"].sum()) == len(task_c.y_test) == 79
        assert int(table["n_desaprobados"].sum()) == int(task_c.y_test.sum()) == 26
        assert (table["n_desaprobados"] <= table["n"]).all()


def test_subgroup_metrics_values_are_proportions(task_c: SimpleNamespace) -> None:
    for table in task_c.fairness.values():
        assert table["precision"].between(0.0, 1.0).all()
        assert table["recall"].between(0.0, 1.0).all()


def test_subgroup_metrics_are_aggregates_only(task_c: SimpleNamespace) -> None:
    """Privacidad: una fila por subgrupo, nunca una por estudiante."""
    for table in task_c.fairness.values():
        assert len(table) == 2 < len(task_c.y_test)


def test_subgroup_metrics_match_manual_computation(task_c: SimpleNamespace) -> None:
    for column, table in task_c.fairness.items():
        for _, row in table.iterrows():
            mask = task_c.x_test[column].to_numpy() == row["group"]
            precision, recall, _, _ = precision_recall_fscore_support_for(
                task_c.y_test.to_numpy()[mask],
                task_c.predictions[mask],
            )
            assert float(row["precision"]) == pytest.approx(precision)
            assert float(row["recall"]) == pytest.approx(recall)


def precision_recall_fscore_support_for(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> tuple[float, float, float, float]:
    """Atajo local: mismas métricas del módulo, calculadas a mano por subconjunto."""
    metrics = evaluate_predictions(y_true, y_pred)
    return (
        float(metrics["precision"]),
        float(metrics["recall"]),
        float(metrics["f1"]),
        float(metrics["accuracy"]),
    )


def test_subgroup_metrics_crafted_example_exact() -> None:
    y_true = np.array([1, 1, 0, 0])
    y_pred = np.array([1, 0, 0, 0])
    groups = pd.Series(["F", "F", "M", "M"])
    table = subgroup_metrics(y_true, y_pred, groups).set_index("group")

    assert int(table.loc["F", "n"]) == 2
    assert int(table.loc["F", "n_desaprobados"]) == 2
    assert float(table.loc["F", "precision"]) == pytest.approx(1.0)
    assert float(table.loc["F", "recall"]) == pytest.approx(0.5)

    assert int(table.loc["M", "n"]) == 2
    assert int(table.loc["M", "n_desaprobados"]) == 0
    assert float(table.loc["M", "precision"]) == 0.0
    assert float(table.loc["M", "recall"]) == 0.0


# ------------------------------------------------------------------------------
# Análisis de brechas y causas
# ------------------------------------------------------------------------------


def test_analyze_fairness_flags_relevant_gap_with_causes() -> None:
    table = pd.DataFrame(
        {
            "group": ["A", "B"],
            "n": [40, 40],
            "n_desaprobados": [8, 16],
            "precision": [0.9, 0.5],
            "recall": [0.8, 0.3],
        }
    )
    info = analyze_fairness({"sex": table})["sex"]
    assert info["relevant"] is True
    assert float(info["recall_gap"]) == pytest.approx(0.5)
    assert float(info["precision_gap"]) == pytest.approx(0.4)
    assert any("desbalanceada" in cause for cause in info["causes"])
    assert any("proxy" in cause for cause in info["causes"])
    assert info["small_groups"] == []


def test_analyze_fairness_accepts_small_gap_without_causes() -> None:
    table = pd.DataFrame(
        {
            "group": ["A", "B"],
            "n": [40, 40],
            "n_desaprobados": [10, 10],
            "precision": [0.9, 0.87],
            "recall": [0.8, 0.79],
        }
    )
    info = analyze_fairness({"sex": table})["sex"]
    assert info["relevant"] is False
    assert float(info["recall_gap"]) < FAIRNESS_GAP_THRESHOLD
    assert info["causes"] == []


def test_analyze_fairness_notes_small_subgroups() -> None:
    table = pd.DataFrame(
        {
            "group": ["GP", "MS"],
            "n": [69, 10],
            "n_desaprobados": [23, 3],
            "precision": [0.84, 1.0],
            "recall": [0.70, 1.0],
        }
    )
    info = analyze_fairness({"school": table})["school"]
    assert info["relevant"] is True
    assert info["small_groups"] == ["MS"]
    assert any("pocos casos (MS)" in cause for cause in info["causes"])


def test_analyze_fairness_respects_custom_threshold() -> None:
    table = pd.DataFrame(
        {
            "group": ["A", "B"],
            "n": [40, 40],
            "n_desaprobados": [10, 10],
            "precision": [0.9, 0.75],
            "recall": [0.8, 0.6],
        }
    )
    assert analyze_fairness({"sex": table}, gap_threshold=0.10)["sex"]["relevant"] is True
    assert analyze_fairness({"sex": table}, gap_threshold=0.50)["sex"]["relevant"] is False


# ------------------------------------------------------------------------------
# Premisas y constantes
# ------------------------------------------------------------------------------


def test_sex_and_school_are_model_predictors() -> None:
    """Premisa de la causa 'proxy': el modelo usa estas variables como entradas."""
    assert "sex" in MODEL_FEATURES
    assert "school" in MODEL_FEATURES


def test_task_c_constants() -> None:
    assert FAIRNESS_GAP_THRESHOLD == 0.10
    assert MIN_SUBGROUP_N == 30


def test_pick_best_model_prefers_f1_then_recall() -> None:
    metrics = {
        "logistic_regression": {"f1": 0.79, "recall": 0.70},
        "random_forest": {"f1": 0.75, "recall": 0.80},
    }
    assert pick_best_model(metrics) == "logistic_regression"

    tied = {
        "logistic_regression": {"f1": 0.75, "recall": 0.70},
        "random_forest": {"f1": 0.75, "recall": 0.80},
    }
    assert pick_best_model(tied) == "random_forest"


def test_fit_real_models_returns_fitted_pipelines(task_c: SimpleNamespace) -> None:
    assert set(task_c.models) == {"logistic_regression", "random_forest"}
    for model in task_c.models.values():
        assert isinstance(model, Pipeline)
        assert hasattr(model, "predict")


def test_recommendation_is_safety_first() -> None:
    assert len(RECOMMENDATION) >= 6
    assert all(line.startswith(("SÍ:", "NO:")) for line in RECOMMENDATION)
    assert sum(line.startswith("NO:") for line in RECOMMENDATION) >= 3

    forbidden = [line for line in RECOMMENDATION if line.startswith("NO:")]
    assert any("administrativas" in line and "revisión humana" in line for line in forbidden)
    assert any("sanciones" in line for line in forbidden)
    assert any("sentencia" in line for line in forbidden)
    assert any("identificables" in line for line in forbidden)

    allowed = [line for line in RECOMMENDATION if line.startswith("SÍ:")]
    assert any("apoyo" in line for line in allowed)
    assert any("docentes" in line for line in allowed)


# ------------------------------------------------------------------------------
# Reporte completo (impresión en pantalla)
# ------------------------------------------------------------------------------


def test_run_task_c_prints_full_report(capsys: pytest.CaptureFixture[str]) -> None:
    result = run_task_c()
    out = capsys.readouterr().out

    assert "Tarea C" in out
    assert "Modelo evaluado: logistic_regression" in out
    assert "por 'sex'" in out
    assert "por 'school'" in out
    assert "n_desaprobados" in out
    assert "Brechas (diferencia relevante desde 10%)" in out
    assert "RELEVANTE" in out
    assert "causa posible" in out
    assert "proxy" in out
    assert "Recomendación de uso (Tarea C.3)" in out
    assert "el modelo sirve para acompañar, no para sancionar" in out
    assert "NO: usar el resultado para decisiones administrativas" in out

    assert set(result) == {"best_model", "fairness", "analysis", "recommendation"}
    assert result["best_model"] == "logistic_regression"
    assert set(result["fairness"]) == {"sex", "school"}
    assert set(result["analysis"]) == {"sex", "school"}
    assert result["recommendation"] == RECOMMENDATION
    for info in result["analysis"].values():
        assert set(info) == {"recall_gap", "precision_gap", "relevant", "small_groups", "causes"}


def test_run_task_c_is_consistent_with_task_b(task_c: SimpleNamespace) -> None:
    result = run_task_c()
    assert result["best_model"] == task_c.best
    for column in SUBGROUP_COLUMNS:
        pd.testing.assert_frame_equal(result["fairness"][column], task_c.fairness[column])
