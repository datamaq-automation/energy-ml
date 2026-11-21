"""src/application/educacion/evaluacion.py — Métricas, línea base y equidad del Issue #5."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)

from src.domain.educacion.modelos import (
    APROBADO,
    DESAPROBADO,
    FAIRNESS_GAP_THRESHOLD,
    MIN_SUBGROUP_N,
)


def evaluate_predictions(
    y_true: pd.Series | np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, object]:
    """Accuracy, precisión, recall, F1 y matriz de confusión con foco en 'desaprobado'."""
    true_array = np.asarray(y_true)
    precision, recall, f1, _ = precision_recall_fscore_support(
        true_array,
        y_pred,
        average="binary",
        pos_label=DESAPROBADO,
        zero_division=0,
    )
    matrix = confusion_matrix(true_array, y_pred, labels=[APROBADO, DESAPROBADO])
    return {
        "accuracy": float(accuracy_score(true_array, y_pred)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "confusion_matrix": matrix.tolist(),
    }


def baseline_predictions(y_train: pd.Series, n: int) -> np.ndarray:
    """Línea base: predice siempre la clase mayoritaria de train (Tarea B.3)."""
    majority = int(y_train.value_counts().idxmax())
    return np.full(n, majority, dtype=int)


def pick_best_model(metrics: dict[str, dict[str, object]]) -> str:
    """Mejor modelo real por F1 de desaprobado (empate → mayor recall)."""
    real_models = ("logistic_regression", "random_forest")
    return max(
        real_models,
        key=lambda name: (float(metrics[name]["f1"]), float(metrics[name]["recall"])),
    )


def subgroup_metrics(
    y_true: pd.Series | np.ndarray,
    y_pred: np.ndarray,
    groups: pd.Series,
) -> pd.DataFrame:
    """Recall y precisión de 'desaprobado' para cada subgrupo (solo agregados)."""
    frame = pd.DataFrame(
        {
            "y_true": np.asarray(y_true),
            "y_pred": np.asarray(y_pred),
            "group": groups.to_numpy(),
        }
    )
    rows: list[dict[str, object]] = []
    for value, subset in frame.groupby("group", sort=True):
        precision, recall, _, _ = precision_recall_fscore_support(
            subset["y_true"],
            subset["y_pred"],
            average="binary",
            pos_label=DESAPROBADO,
            zero_division=0,
        )
        rows.append(
            {
                "group": value,
                "n": int(len(subset)),
                "n_desaprobados": int((subset["y_true"] == DESAPROBADO).sum()),
                "precision": float(precision),
                "recall": float(recall),
            }
        )
    return pd.DataFrame(rows)


def analyze_fairness(
    tables: dict[str, pd.DataFrame],
    gap_threshold: float = FAIRNESS_GAP_THRESHOLD,
) -> dict[str, dict[str, object]]:
    """Detecta brechas relevantes por subgrupo y enumera causas posibles (Tarea C.2).

    Causas consideradas: subgrupos chicos (métrica ruidosa), desbalance de la
    etiqueta entre subgrupos, y el uso de la propia variable como predictora
    (puede actuar como proxy de otras características).
    """
    analysis: dict[str, dict[str, object]] = {}
    for column, table in tables.items():
        recall_gap = float(table["recall"].max() - table["recall"].min())
        precision_gap = float(table["precision"].max() - table["precision"].min())
        small_groups = [str(value) for value in table.loc[table["n"] < MIN_SUBGROUP_N, "group"]]
        positive_rates = table["n_desaprobados"] / table["n"]
        rate_gap = float(positive_rates.max() - positive_rates.min())
        relevant = recall_gap >= gap_threshold or precision_gap >= gap_threshold

        causes: list[str] = []
        if small_groups:
            causes.append(
                f"subgrupo con pocos casos ({', '.join(small_groups)}): la métrica es ruidosa"
            )
        if rate_gap >= gap_threshold:
            causes.append(
                "la proporción de desaprobados difiere entre subgrupos "
                f"({positive_rates.min():.0%} vs {positive_rates.max():.0%}): "
                "la etiqueta está desbalanceada por subgrupo"
            )
        if relevant:
            causes.append(
                f"'{column}' también es variable del modelo: puede actuar como proxy "
                "de otras características"
            )

        analysis[column] = {
            "recall_gap": recall_gap,
            "precision_gap": precision_gap,
            "relevant": relevant,
            "small_groups": small_groups,
            "causes": causes,
        }
    return analysis
