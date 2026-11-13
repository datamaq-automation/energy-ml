"""tests/educacion/test_fail_risk_tarea_b.py — Cobertura total de la Tarea B (Issue #5)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from educacion.fail_risk import (
    APROBADO,
    CATEGORICAL_FEATURES,
    DESAPROBADO,
    FAIL_THRESHOLD,
    MODEL_FEATURES,
    NUMERIC_FEATURES,
    SEED,
    TEST_SIZE,
    baseline_predictions,
    build_logistic_regression,
    build_random_forest,
    build_target,
    evaluate_predictions,
    load_students,
    run_task_b,
    select_model_features,
    split_train_test,
)

#: Las 18 variables permitidas por la sección 2 del issue para el momento declarado.
ESPERADAS = {
    "G1",
    "studytime",
    "failures",
    "absences",
    "higher",
    "Medu",
    "Fedu",
    "school",
    "sex",
    "age",
    "address",
    "famsup",
    "schoolsup",
    "internet",
    "goout",
    "Dalc",
    "Walc",
    "health",
}


@pytest.fixture(scope="module")
def students() -> pd.DataFrame:
    """Dataset real una sola vez para toda la suite de la Tarea B."""
    return load_students()


@pytest.fixture(scope="module")
def split(
    students: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split 80/20 estratificado, calculado una sola vez por sesión."""
    return split_train_test(students)


# ------------------------------------------------------------------------------
# Etiqueta: desaprobado = G3 < 10
# ------------------------------------------------------------------------------


def test_build_target_matches_issue_threshold(students: pd.DataFrame) -> None:
    target = build_target(students)
    assert len(target) == 395
    assert int(target.sum()) == 130
    assert set(target.unique()) == {APROBADO, DESAPROBADO}
    assert target.name == "desaprobado"


def test_build_target_only_depends_on_g3(students: pd.DataFrame) -> None:
    base = build_target(students)

    tweaked = students.copy()
    tweaked["G1"] = 20 - tweaked["G1"]
    tweaked["studytime"] = 4
    tweaked["absences"] = 0
    pd.testing.assert_series_equal(build_target(tweaked), base)

    failing_row = base[base == DESAPROBADO].index[0]
    raised = students.copy()
    raised.loc[failing_row, "G3"] = FAIL_THRESHOLD + 5
    changed = build_target(raised)
    assert changed.loc[failing_row] == APROBADO
    pd.testing.assert_series_equal(
        changed.drop(labels=[failing_row]),
        base.drop(labels=[failing_row]),
    )


def test_build_target_requires_g3(students: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="G3 es obligatoria"):
        build_target(students.drop(columns=["G3"]))


# ------------------------------------------------------------------------------
# Variables del modelo (cero fuga de datos)
# ------------------------------------------------------------------------------


def test_model_features_match_issue_allowed_set() -> None:
    assert set(MODEL_FEATURES) == ESPERADAS
    assert len(MODEL_FEATURES) == 18


def test_model_features_exclude_g2_and_g3() -> None:
    assert "G3" not in MODEL_FEATURES, "G3 es la etiqueta y jamás puede ser entrada"
    assert "G2" not in MODEL_FEATURES, "G2 no se conoce en el momento de predicción"


def test_feature_partition_is_complete_and_disjoint() -> None:
    assert set(CATEGORICAL_FEATURES) | set(NUMERIC_FEATURES) == set(MODEL_FEATURES)
    assert not set(CATEGORICAL_FEATURES) & set(NUMERIC_FEATURES)
    assert set(CATEGORICAL_FEATURES) <= ESPERADAS


def test_select_model_features_missing_column_raises(students: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="Faltan columnas requeridas"):
        select_model_features(students.drop(columns=["G1"]))


# ------------------------------------------------------------------------------
# Split 80/20 estratificado, antes de transformar
# ------------------------------------------------------------------------------


def test_split_is_80_20(
    split: tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
) -> None:
    x_train, x_test, y_train, y_test = split
    assert len(x_train) == 316
    assert len(x_test) == 79
    assert len(x_train) + len(x_test) == 395
    assert len(x_test) / 395 == pytest.approx(TEST_SIZE, abs=0.01)
    assert len(y_train) == len(x_train) and len(y_test) == len(x_test)


def test_split_is_stratified_by_label(
    split: tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
) -> None:
    _, _, y_train, y_test = split
    global_rate = 130 / 395
    assert float(y_train.mean()) == pytest.approx(global_rate, abs=0.01)
    assert float(y_test.mean()) == pytest.approx(global_rate, abs=0.01)


def test_split_is_deterministic(students: pd.DataFrame) -> None:
    first = split_train_test(students)
    second = split_train_test(students)
    for a, b in zip(first, second, strict=True):
        assert a.index.tolist() == b.index.tolist()


def test_split_indices_are_disjoint(
    split: tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
) -> None:
    x_train, x_test, _, _ = split
    assert set(x_train.index).isdisjoint(set(x_test.index))
    assert set(x_train.index) | set(x_test.index) == set(range(395))


def test_split_feature_matrix_has_no_leak_columns(
    split: tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
) -> None:
    x_train, x_test, _, _ = split
    for frame in (x_train, x_test):
        assert "G3" not in frame.columns
        assert "G2" not in frame.columns
        assert set(frame.columns) == ESPERADAS


def test_scaler_fits_only_on_train(
    split: tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
) -> None:
    """Si alguien transformara antes de partir, la media sería la del dataset completo."""
    x_train, _, y_train, _ = split
    pipeline = build_logistic_regression()
    pipeline.fit(x_train, y_train)
    scaler = pipeline.named_steps["pre"].named_transformers_["num"].named_steps["scaler"]
    train_mean = x_train.loc[:, list(NUMERIC_FEATURES)].mean().to_numpy()
    full_mean = load_students().loc[:, list(NUMERIC_FEATURES)].mean().to_numpy()
    assert np.allclose(scaler.mean_, train_mean)
    assert not np.allclose(scaler.mean_, full_mean)


def test_encoder_ignores_unseen_category(students: pd.DataFrame) -> None:
    gp_only = students[students["school"] == "GP"]
    x_gp = select_model_features(gp_only)
    y_gp = build_target(gp_only)
    pipeline = build_logistic_regression()
    pipeline.fit(x_gp, y_gp)

    onehot = pipeline.named_steps["pre"].named_transformers_["cat"].named_steps["onehot"]
    school_idx = CATEGORICAL_FEATURES.index("school")
    assert list(onehot.categories_[school_idx]) == ["GP"]

    ms_rows = select_model_features(students[students["school"] == "MS"])
    predictions = pipeline.predict(ms_rows)
    assert set(np.unique(predictions)) <= {APROBADO, DESAPROBADO}


# ------------------------------------------------------------------------------
# Línea base
# ------------------------------------------------------------------------------


def test_baseline_predicts_train_majority(
    split: tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
) -> None:
    _, x_test, y_train, _ = split
    predictions = baseline_predictions(y_train, len(x_test))
    majority = int(y_train.value_counts().idxmax())
    assert set(predictions.tolist()) == {majority}
    assert majority == APROBADO, "la clase mayoritaria es 'aprobado'"


def test_baseline_has_zero_recall_for_failing(
    split: tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
) -> None:
    _, x_test, y_train, y_test = split
    metrics = evaluate_predictions(y_test, baseline_predictions(y_train, len(x_test)))
    assert metrics["recall"] == 0.0
    assert metrics["f1"] == 0.0
    assert metrics["accuracy"] == pytest.approx(float((y_test == APROBADO).mean()))


# ------------------------------------------------------------------------------
# Métricas
# ------------------------------------------------------------------------------


def test_evaluate_predictions_exact_values() -> None:
    y_true = np.array([APROBADO, APROBADO, DESAPROBADO, DESAPROBADO])
    y_pred = np.array([APROBADO, DESAPROBADO, DESAPROBADO, DESAPROBADO])
    metrics = evaluate_predictions(y_true, y_pred)
    assert metrics["accuracy"] == pytest.approx(0.75)
    assert metrics["precision"] == pytest.approx(2 / 3)
    assert metrics["recall"] == pytest.approx(1.0)
    assert metrics["f1"] == pytest.approx(0.8)
    assert metrics["confusion_matrix"] == [[1, 1], [0, 2]]


def test_evaluate_confusion_matrix_sums_to_sample_size(
    split: tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
) -> None:
    _, x_test, y_train, y_test = split
    metrics = evaluate_predictions(y_test, baseline_predictions(y_train, len(x_test)))
    matrix = np.asarray(metrics["confusion_matrix"])
    assert matrix.shape == (2, 2)
    assert int(matrix.sum()) == len(y_test)


# ------------------------------------------------------------------------------
# Modelos
# ------------------------------------------------------------------------------


def test_random_forest_hyperparameters() -> None:
    forest = build_random_forest()
    clf = forest.named_steps["clf"]
    assert clf.n_estimators == 200
    assert clf.class_weight == "balanced"
    assert clf.random_state == SEED == 42


def test_logistic_regression_hyperparameters() -> None:
    logistic = build_logistic_regression()
    assert [name for name, _ in logistic.steps] == ["pre", "clf"]
    clf = logistic.named_steps["clf"]
    assert clf.random_state == SEED == 42
    assert clf.max_iter >= 1000


def test_logistic_regression_converges(
    split: tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
) -> None:
    x_train, _, y_train, _ = split
    pipeline = build_logistic_regression()
    pipeline.fit(x_train, y_train)
    clf = pipeline.named_steps["clf"]
    assert int(clf.n_iter_[0]) < clf.max_iter, "sin ConvergenceWarning"


def test_pipelines_never_expose_g2_or_g3(
    split: tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
) -> None:
    x_train, _, y_train, _ = split
    for builder in (build_logistic_regression, build_random_forest):
        pipeline = builder()
        pipeline.fit(x_train, y_train)
        names = pipeline.named_steps["pre"].get_feature_names_out()
        joined = " ".join(names)
        assert "G3" not in joined
        assert "G2" not in joined


def test_pipelines_are_reproducible(
    split: tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
) -> None:
    x_train, x_test, y_train, _ = split
    for builder in (build_logistic_regression, build_random_forest):
        first = builder()
        second = builder()
        first.fit(x_train, y_train)
        second.fit(x_train, y_train)
        assert np.array_equal(first.predict(x_test), second.predict(x_test))


def test_models_beat_baseline_recall(
    split: tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
) -> None:
    """Checklist del issue: el modelo supera a la línea base en recall de desaprobados."""
    x_train, x_test, y_train, y_test = split
    baseline = evaluate_predictions(y_test, baseline_predictions(y_train, len(x_test)))

    logistic = build_logistic_regression()
    logistic.fit(x_train, y_train)
    logistic_metrics = evaluate_predictions(y_test, logistic.predict(x_test))

    forest = build_random_forest()
    forest.fit(x_train, y_train)
    forest_metrics = evaluate_predictions(y_test, forest.predict(x_test))

    assert float(logistic_metrics["recall"]) > float(baseline["recall"])
    assert float(forest_metrics["recall"]) > float(baseline["recall"])
    for metrics in (logistic_metrics, forest_metrics):
        assert float(metrics["accuracy"]) >= float(baseline["accuracy"]) - 0.2
        assert 0.0 <= float(metrics["precision"]) <= 1.0


# ------------------------------------------------------------------------------
# Reporte completo (impresión en pantalla)
# ------------------------------------------------------------------------------


def test_run_task_b_prints_full_report(capsys: pytest.CaptureFixture[str]) -> None:
    result = run_task_b()
    out = capsys.readouterr().out

    assert "Tarea B" in out
    assert "Momento de predicción" in out
    assert "Split 80/20 estratificado ANTES de transformar" in out
    assert "random_state=42" in out
    assert "línea base" in out
    assert "regresión logística" in out
    assert "bosque aleatorio" in out
    assert "Matriz de confusión" in out
    assert "Mejor modelo (mayor F1 de desaprobado)" in out
    assert "¿supera a la línea base en recall de desaprobados? Sí" in out

    assert result["n_train"] == 316 and result["n_test"] == 79
    assert set(result["metrics"]) == {"baseline", "logistic_regression", "random_forest"}
    assert result["best_model"] in {"logistic_regression", "random_forest"}
    assert result["beats_baseline_recall"] is True
    assert float(result["metrics"][result["best_model"]]["recall"]) > float(
        result["metrics"]["baseline"]["recall"]
    )
    for model_metrics in result["metrics"].values():
        assert set(model_metrics) == {"accuracy", "precision", "recall", "f1", "confusion_matrix"}
