"""tests/unit/logistica/test_logistics_pipeline.py — Pruebas de las Tareas A, B y C de logística y reglas anti-fuga."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.domain.logistica.models import (
    CATEGORICAL_FEATURES,
    FORBIDDEN_COLUMNS,
    KMEANS_FEATURES,
    NUMERIC_FEATURES,
    describe_cluster_business_profile,
    validate_no_data_leakage,
)
from src.infrastructure.cli.analizar_logistica import main as cli_main
from src.infrastructure.sklearn.logistics_pipeline import (
    load_and_prepare_orders,
    run_task_a_clustering,
    run_task_b_supervised,
    run_task_c_error_analysis,
    save_confusion_matrix_plot,
    save_elbow_and_silhouette_plot,
    split_and_preprocess,
)


def _create_synthetic_orders_csv(csv_path: Path, n_rows: int = 240) -> Path:
    """Genera un dataset sintético con la estructura exacta de DataCo Supply Chain."""
    rng = np.random.default_rng(42)
    modes = rng.choice(
        ["First Class", "Second Class", "Same Day", "Standard Class"],
        size=n_rows,
        p=[0.20, 0.20, 0.10, 0.50],
    )
    sched_map = {"First Class": 1, "Second Class": 2, "Same Day": 0, "Standard Class": 4}
    scheduled = np.array([sched_map[m] for m in modes])
    late = np.where(
        np.isin(modes, ["First Class", "Second Class"]),
        1,
        rng.binomial(1, 0.15, size=n_rows),
    )

    df = pd.DataFrame(
        {
            "Days for shipping (real)": scheduled + late * 2,
            "Days for shipment (scheduled)": scheduled,
            "Delivery Status": np.where(late == 1, "Late delivery", "Shipping on time"),
            "Late_delivery_risk": late,
            "Order Status": np.where(late == 1, "PENDING", "COMPLETE"),
            "shipping date (DateOrders)": ["1/18/2018 12:00"] * n_rows,
            "order date (DateOrders)": [
                f"1/{(i % 28) + 1}/2018 {(i * 3) % 24}:15" for i in range(n_rows)
            ],
            "Order Item Quantity": rng.integers(1, 6, size=n_rows),
            "Sales": rng.uniform(50.0, 400.0, size=n_rows).round(2),
            "Order Item Discount Rate": rng.uniform(0.0, 0.25, size=n_rows).round(2),
            "Latitude": rng.choice([18.22, 37.09], size=n_rows),
            "Longitude": rng.choice([-66.59, -95.71], size=n_rows),
            "Shipping Mode": modes,
            "Market": rng.choice(["LATAM", "Europe", "USCA"], size=n_rows),
            "Order Region": rng.choice(["Central America", "Western Europe"], size=n_rows),
            "Customer Segment": rng.choice(["Consumer", "Corporate"], size=n_rows),
        }
    )
    df.to_csv(csv_path, index=False, encoding="latin-1")
    return csv_path


def test_forbidden_columns_rejected_and_removed(tmp_path: Path) -> None:
    """Regla 1: Ninguna variable prohibida puede entrar al modelo ni aparecer en X."""
    for forbidden in FORBIDDEN_COLUMNS:
        with pytest.raises(ValueError, match="Data leakage detectado"):
            validate_no_data_leakage(["Sales", forbidden])

    csv_path = _create_synthetic_orders_csv(tmp_path / "pedidos.csv")
    df = load_and_prepare_orders(csv_path)

    for forbidden in FORBIDDEN_COLUMNS:
        if forbidden != "Late_delivery_risk":
            assert forbidden not in df.columns

    _, _, _, _, feature_names, x_test_df = split_and_preprocess(df)
    for forbidden in FORBIDDEN_COLUMNS:
        assert forbidden not in x_test_df.columns
        assert not any(forbidden.lower() in f.lower() for f in feature_names)


def test_split_happens_before_scaling(tmp_path: Path) -> None:
    """Regla 2: El split 80/20 se hace antes de ajustar StandardScaler e imputadores."""
    csv_path = _create_synthetic_orders_csv(tmp_path / "pedidos.csv", n_rows=200)
    df = load_and_prepare_orders(csv_path)
    x_train, x_test, y_train, y_test, _, _ = split_and_preprocess(df)

    assert len(x_train) == 160
    assert len(x_test) == 40
    assert len(y_train) == 160
    assert len(y_test) == 40

    num_count = len(NUMERIC_FEATURES)
    train_means = np.abs(x_train[:, :num_count].mean(axis=0))
    assert np.all(train_means < 1e-10)


def test_task_a_clustering_and_plots(tmp_path: Path) -> None:
    """Tarea A: K-means para k en 2..8, codo, silueta y perfiles de negocio."""
    csv_path = _create_synthetic_orders_csv(tmp_path / "pedidos.csv", n_rows=160)
    df = load_and_prepare_orders(csv_path)
    metrics, profiles = run_task_a_clustering(
        df, k_values=(2, 3, 4, 5), best_k=4, silhouette_sample_size=100
    )

    assert [m.k for m in metrics] == [2, 3, 4, 5]
    assert metrics[0].inertia > metrics[-1].inertia
    assert all(-1.0 <= m.silhouette <= 1.0 for m in metrics)
    assert len(profiles) == 4
    assert sum(p.order_count for p in profiles) == 160

    plot_path = tmp_path / "elbow.png"
    save_elbow_and_silhouette_plot(metrics, best_k=4, output_path=plot_path)
    assert plot_path.exists() and plot_path.stat().st_size > 0

    assert "mayoristas" in describe_cluster_business_profile(3.0, 4.5, 37.0)
    assert "rápidos" in describe_cluster_business_profile(1.2, 1.5, 18.5)
    assert "estándar" in describe_cluster_business_profile(4.0, 1.5, 37.0)
    assert len(KMEANS_FEATURES) == 5
    assert len(CATEGORICAL_FEATURES) == 4


def test_task_b_and_c_supervised_and_error_analysis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Tareas B y C: Modelos supervisados superan línea base en recall y desglosan errores."""
    csv_path = _create_synthetic_orders_csv(tmp_path / "pedidos.csv", n_rows=240)
    df = load_and_prepare_orders(csv_path)
    x_train, x_test, y_train, y_test, feat_names, x_test_df = split_and_preprocess(df)

    results, importances, best_preds = run_task_b_supervised(
        x_train, x_test, y_train, y_test, feat_names, tree_max_depth=4
    )
    assert len(results) == 4
    baseline_zero = results[0]
    log_reg = results[2]
    tree_model = results[3]

    assert tree_model.recall > baseline_zero.recall
    assert log_reg.recall > baseline_zero.recall
    assert tree_model.f1 > 0.5
    assert len(importances) > 0

    cm_path = tmp_path / "cm.png"
    save_confusion_matrix_plot(tree_model, output_path=cm_path)
    assert cm_path.exists() and cm_path.stat().st_size > 0

    segments = run_task_c_error_analysis(x_test_df, y_test, best_preds, "Shipping Mode")
    assert len(segments) >= 2
    assert all(0.0 <= s.recall <= 1.0 for s in segments)

    monkeypatch.setattr(
        "sys.argv",
        [
            "analizar_logistica.py",
            "--csv",
            str(csv_path),
            "--output-dir",
            str(tmp_path),
            "--best-k",
            "3",
            "--max-depth",
            "4",
        ],
    )
    cli_main()
