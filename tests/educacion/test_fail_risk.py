"""tests/educacion/test_fail_risk.py — Cobertura total de la Tarea A (K-means) del Issue #5."""

from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from educacion.fail_risk import (
    CLUSTER_FEATURES,
    DATA_PATH,
    FAIL_THRESHOLD,
    K_MAX,
    K_MIN,
    SEED,
    choose_k,
    compute_k_metrics,
    describe_groups,
    failing_rates_by_group,
    fit_kmeans,
    load_students,
    plot_elbow_silhouette,
    run_task_a,
    scale_features,
    select_cluster_features,
)

matplotlib.use("Agg", force=True)

RAIZ = Path(__file__).resolve().parents[2]
MODULO = RAIZ / "educacion" / "fail_risk.py"


@pytest.fixture(scope="module")
def students() -> pd.DataFrame:
    """Dataset real una sola vez para toda la suite de la Tarea A."""
    return load_students()


@pytest.fixture(scope="module")
def clustering(students: pd.DataFrame) -> SimpleNamespace:
    """Pipeline completo de la Tarea A, calculado una sola vez por sesión."""
    features = select_cluster_features(students)
    scaled = scale_features(features)
    k_values, inertias, silhouettes = compute_k_metrics(scaled)
    best_k = choose_k(k_values, silhouettes)
    labels = fit_kmeans(scaled, best_k)
    return SimpleNamespace(
        df=students,
        features=features,
        scaled=scaled,
        k_values=k_values,
        inertias=inertias,
        silhouettes=silhouettes,
        best_k=best_k,
        labels=labels,
    )


# ------------------------------------------------------------------------------
# Carga y validación del dataset
# ------------------------------------------------------------------------------


def test_load_students_shape_and_quality(students: pd.DataFrame) -> None:
    assert students.shape == (395, 33)
    assert int(students.isna().sum().sum()) == 0
    for column in ("G1", "G2", "G3", *CLUSTER_FEATURES[1:]):
        assert column in students.columns


def test_load_students_missing_columns_raises(tmp_path: Path) -> None:
    bad = tmp_path / "incompleto.csv"
    bad.write_text("G1;studytime\n5;2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Faltan columnas requeridas"):
        load_students(bad)


def test_load_students_non_numeric_g3_raises(tmp_path: Path) -> None:
    bad = tmp_path / "g3_texto.csv"
    bad.write_text(
        "G1;studytime;failures;absences;G3\n5;2;0;4;buena\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="G3 debe ser numérica"):
        load_students(bad)


def test_data_path_points_to_local_dataset() -> None:
    assert DATA_PATH.exists()
    assert DATA_PATH.name == "student-mat.csv"
    assert "educacion" in DATA_PATH.parts


# ------------------------------------------------------------------------------
# Selección de variables (cero fuga de datos)
# ------------------------------------------------------------------------------


def test_cluster_features_are_exactly_the_allowed_set(clustering: SimpleNamespace) -> None:
    assert list(clustering.features.columns) == list(CLUSTER_FEATURES)


def test_cluster_features_exclude_g2_and_g3(clustering: SimpleNamespace) -> None:
    columns = set(clustering.features.columns)
    assert "G3" not in columns, "G3 es la etiqueta y jamás puede ser entrada"
    assert "G2" not in columns, "G2 no se conoce en el momento de predicción declarado"


def test_select_cluster_features_does_not_mutate_source(students: pd.DataFrame) -> None:
    before = list(students.columns)
    select_cluster_features(students)
    assert list(students.columns) == before


# ------------------------------------------------------------------------------
# Escalado
# ------------------------------------------------------------------------------


def test_scale_features_zero_mean_unit_std(clustering: SimpleNamespace) -> None:
    assert np.allclose(clustering.scaled.mean(axis=0), 0.0, atol=1e-6)
    assert np.allclose(clustering.scaled.std(axis=0), 1.0, atol=1e-6)


def test_scale_features_preserves_shape(clustering: SimpleNamespace) -> None:
    assert clustering.scaled.shape == clustering.features.shape


# ------------------------------------------------------------------------------
# Métricas de k (codo y silueta)
# ------------------------------------------------------------------------------


def test_k_metrics_covers_declared_range(clustering: SimpleNamespace) -> None:
    assert clustering.k_values == [K_MIN, K_MIN + 1, K_MIN + 2, K_MIN + 3, K_MAX]
    assert len(clustering.inertias) == len(clustering.silhouettes) == len(clustering.k_values) == 5


def test_k_metrics_inertia_strictly_decreases(clustering: SimpleNamespace) -> None:
    inertias = clustering.inertias
    assert all(a > b for a, b in zip(inertias, inertias[1:], strict=False))


def test_k_metrics_silhouettes_are_finite_and_bounded(clustering: SimpleNamespace) -> None:
    for score in clustering.silhouettes:
        assert np.isfinite(score)
        assert -1.0 < score < 1.0


def test_k_metrics_are_deterministic(students: pd.DataFrame) -> None:
    scaled = scale_features(select_cluster_features(students))
    first = compute_k_metrics(scaled)
    second = compute_k_metrics(scaled)
    assert first == second
    assert SEED == 42


def test_compute_k_metrics_rejects_empty_range(clustering: SimpleNamespace) -> None:
    with pytest.raises(ValueError, match="k_values no puede estar vacío"):
        compute_k_metrics(clustering.scaled, k_values=range(0, 0))


# ------------------------------------------------------------------------------
# Elección de k
# ------------------------------------------------------------------------------


def test_choose_k_matches_max_silhouette(clustering: SimpleNamespace) -> None:
    expected = clustering.k_values[int(np.argmax(clustering.silhouettes))]
    assert choose_k(clustering.k_values, clustering.silhouettes) == expected
    assert K_MIN <= clustering.best_k <= K_MAX


def test_choose_k_rejects_mismatched_inputs() -> None:
    with pytest.raises(ValueError, match="listas no vacías"):
        choose_k([], [])


# ------------------------------------------------------------------------------
# K-means final
# ------------------------------------------------------------------------------


def test_fit_kmeans_assigns_every_student(clustering: SimpleNamespace) -> None:
    assert len(clustering.labels) == len(clustering.df)
    assert set(clustering.labels.tolist()) == set(range(clustering.best_k))


def test_fit_kmeans_is_reproducible(clustering: SimpleNamespace) -> None:
    again = fit_kmeans(clustering.scaled, clustering.best_k)
    assert np.array_equal(clustering.labels, again)


# ------------------------------------------------------------------------------
# Descripción educativa de grupos (agregados, sin datos individuales)
# ------------------------------------------------------------------------------


def test_describe_groups_has_one_description_per_group(clustering: SimpleNamespace) -> None:
    descriptions = describe_groups(clustering.features, clustering.labels)
    assert set(descriptions.index) == set(range(clustering.best_k))
    assert all(isinstance(text, str) and text for text in descriptions)


def test_describe_groups_references_performance_data(clustering: SimpleNamespace) -> None:
    descriptions = describe_groups(clustering.features, clustering.labels)
    assert all("G1" in text for text in descriptions)


def test_describe_groups_is_aggregate_only(clustering: SimpleNamespace) -> None:
    descriptions = describe_groups(clustering.features, clustering.labels)
    assert len(descriptions) == clustering.best_k < len(clustering.df)


# ------------------------------------------------------------------------------
# Proporción de desaprobados por grupo (solo interpretación, tras agrupar)
# ------------------------------------------------------------------------------


def test_failing_rates_are_proportions(clustering: SimpleNamespace) -> None:
    rates = failing_rates_by_group(clustering.df, clustering.labels)
    assert len(rates) == clustering.best_k
    assert not rates.isna().any()
    assert rates.between(0.0, 1.0).all()


def test_failing_rates_match_manual_threshold(clustering: SimpleNamespace) -> None:
    rates = failing_rates_by_group(clustering.df, clustering.labels)
    manual = (
        pd.Series((clustering.df["G3"] < FAIL_THRESHOLD).to_numpy(), dtype=float)
        .groupby(clustering.labels)
        .mean()
    )
    assert np.array_equal(rates.index.to_numpy(), manual.index.to_numpy())
    assert np.allclose(rates.to_numpy(), manual.to_numpy())


def test_failing_rates_weighted_average_matches_global_rate(clustering: SimpleNamespace) -> None:
    rates = failing_rates_by_group(clustering.df, clustering.labels)
    counts = np.bincount(clustering.labels, minlength=clustering.best_k)
    weighted = float(np.average(rates.to_numpy(), weights=counts))
    global_rate = float((clustering.df["G3"] < FAIL_THRESHOLD).mean())
    assert weighted == pytest.approx(global_rate)


def test_fail_threshold_matches_issue_label() -> None:
    assert FAIL_THRESHOLD == 10
    assert int((load_students()["G3"] < FAIL_THRESHOLD).sum()) == 130


# ------------------------------------------------------------------------------
# Gráficos: solo pantalla, nunca archivos
# ------------------------------------------------------------------------------


def test_plot_elbow_shows_without_saving(monkeypatch: pytest.MonkeyPatch) -> None:
    shown: list[int] = []

    def _fail_savefig(*args: object, **kwargs: object) -> None:
        raise AssertionError("La Tarea A no debe guardar gráficos en disco")

    monkeypatch.setattr(plt, "show", lambda: shown.append(1))
    monkeypatch.setattr(plt, "savefig", _fail_savefig)
    plot_elbow_silhouette([2, 3, 4], [100.0, 80.0, 60.0], [0.4, 0.5, 0.45])
    assert shown == [1]


# ------------------------------------------------------------------------------
# Ejecución completa (impresión en pantalla)
# ------------------------------------------------------------------------------


def test_run_task_a_prints_full_report(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shown: list[int] = []
    monkeypatch.setattr(plt, "show", lambda: shown.append(1))

    result = run_task_a()

    out = capsys.readouterr().out
    assert "Tarea A" in out
    assert "Variables de agrupamiento" in out
    assert "silueta" in out
    assert "k elegido" in out
    assert "Grupos descritos en lenguaje educativo" in out
    assert "Proporción de desaprobados por grupo" in out
    assert shown == [1]

    assert result["best_k"] in result["k_values"]
    assert len(result["labels"]) == 395
    assert len(result["descriptions"]) == result["best_k"]
    assert len(result["failing_rates"]) == result["best_k"]


# ------------------------------------------------------------------------------
# Reglas de código: sin rutas absolutas, semilla fija
# ------------------------------------------------------------------------------


def test_source_has_no_absolute_paths() -> None:
    source = MODULO.read_text(encoding="utf-8")
    assert not re.search(r"[A-Za-z]:[\\/]", source), "rutas absolutas prohibidas (regla 8)"
    assert "/home/" not in source
    assert "__file__" in source, "DATA_PATH debe derivarse de __file__"


def test_source_declares_seed_and_data_path_constants() -> None:
    source = MODULO.read_text(encoding="utf-8")
    assert "SEED = 42" in source
    assert "datos" in source and "educacion" in source and "student-mat.csv" in source
