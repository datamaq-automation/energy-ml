"""tests/unit/mantenimiento/test_agrupamiento.py — Pruebas del K-means de mantenimiento."""

import numpy as np
import pandas as pd
import pytest

from src.domain.mantenimiento.models import NUMERIC_FEATURES
from src.infrastructure.sklearn.mantenimiento_agrupamiento import (
    K_RANGE,
    best_k_by_silhouette,
    compute_k_metrics,
    profile_clusters,
    scale_telemetry,
)


@pytest.fixture
def machines() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 300
    return pd.DataFrame(
        {
            "Air temperature [K]": rng.normal(300, 2, n),
            "Process temperature [K]": rng.normal(310, 2, n),
            "Rotational speed [rpm]": rng.normal(1500, 100, n),
            "Torque [Nm]": rng.normal(40, 5, n),
            "Tool wear [min]": rng.integers(0, 250, n),
            "Machine failure": [1 if i % 15 == 0 else 0 for i in range(n)],
        }
    )


def test_scaling_uses_only_telemetry(machines: pd.DataFrame) -> None:
    scaled = scale_telemetry(machines)
    assert scaled.shape == (len(machines), len(NUMERIC_FEATURES))
    assert scaled.mean(axis=0) == pytest.approx(0.0, abs=1e-9)


def test_metrics_cover_k_range(machines: pd.DataFrame) -> None:
    metrics = compute_k_metrics(scale_telemetry(machines))
    assert [item.k for item in metrics] == list(K_RANGE)
    assert all(-1.0 <= item.silhouette <= 1.0 for item in metrics)


def test_metrics_are_reproducible(machines: pd.DataFrame) -> None:
    scaled = scale_telemetry(machines)
    first = compute_k_metrics(scaled)
    second = compute_k_metrics(scaled)
    assert [m.inertia for m in first] == pytest.approx([m.inertia for m in second])


def test_best_k_has_highest_silhouette(machines: pd.DataFrame) -> None:
    metrics = compute_k_metrics(scale_telemetry(machines))
    best = best_k_by_silhouette(metrics)
    assert max(m.silhouette for m in metrics) == next(m.silhouette for m in metrics if m.k == best)


def test_profile_has_one_row_per_cluster(machines: pd.DataFrame) -> None:
    profile = profile_clusters(machines, scale_telemetry(machines), k=3)
    assert len(profile) == 3
    assert profile["size"].sum() == len(machines)
    assert profile["failure_rate"].between(0.0, 1.0).all()
