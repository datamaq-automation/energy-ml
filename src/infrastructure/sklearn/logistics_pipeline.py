"""src/infrastructure/sklearn/logistics_pipeline.py — Pipeline de aprendizaje no supervisado y supervisado para logística."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from src.domain.logistica.models import (
    CATEGORICAL_FEATURES,
    FORBIDDEN_COLUMNS,
    KMEANS_FEATURES,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
    ClusterMetric,
    ClusterProfile,
    SegmentRecall,
    SupervisedModelMetrics,
    describe_cluster_business_profile,
    validate_no_data_leakage,
)

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RANDOM_STATE: int = 42


def load_and_prepare_orders(csv_path: Path, max_rows: int | None = None) -> pd.DataFrame:
    """Carga el CSV de pedidos, desglosa la fecha del pedido y elimina columnas prohibidas."""
    df = pd.read_csv(csv_path, encoding="latin-1", nrows=max_rows)
    order_dt = pd.to_datetime(df["order date (DateOrders)"], format="mixed")
    df["order_month"] = order_dt.dt.month
    df["order_dayofweek"] = order_dt.dt.day_of_week
    df["order_hour"] = order_dt.dt.hour

    drop_cols = [c for c in FORBIDDEN_COLUMNS if c != TARGET_COLUMN and c in df.columns]
    cleaned = df.drop(columns=drop_cols)
    feature_cols = [c for c in cleaned.columns if c != TARGET_COLUMN]
    validate_no_data_leakage(feature_cols)
    return cleaned


def run_task_a_clustering(
    df: pd.DataFrame,
    k_values: tuple[int, ...] = (2, 3, 4, 5, 6, 7, 8),
    best_k: int = 5,
    silhouette_sample_size: int | None = 10000,
) -> tuple[list[ClusterMetric], list[ClusterProfile]]:
    """Ejecuta Tarea A: escalado StandardScaler, K-means para k en [2..8] y perfilado de negocio."""
    validate_no_data_leakage(KMEANS_FEATURES)
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(df[list(KMEANS_FEATURES)])

    metrics: list[ClusterMetric] = []
    best_labels: np.ndarray | None = None
    sample_n = (
        min(silhouette_sample_size, len(x_scaled)) if silhouette_sample_size is not None else None
    )

    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = kmeans.fit_predict(x_scaled)
        sil = float(
            silhouette_score(x_scaled, labels, sample_size=sample_n, random_state=RANDOM_STATE)
        )
        metrics.append(ClusterMetric(k=k, inertia=float(kmeans.inertia_), silhouette=sil))
        if k == best_k:
            best_labels = labels

    if best_labels is None:
        kmeans = KMeans(n_clusters=best_k, random_state=RANDOM_STATE, n_init=10)
        best_labels = kmeans.fit_predict(x_scaled)

    profiles = build_cluster_profiles(df, best_labels)
    return metrics, profiles


def build_cluster_profiles(df: pd.DataFrame, labels: np.ndarray) -> list[ClusterProfile]:
    """Construye el resumen de cada grupo e interpreta la proporción de retrasos post-hoc."""
    work = df[list(KMEANS_FEATURES) + [TARGET_COLUMN, "Shipping Mode"]].copy()
    work["cluster"] = labels
    profiles: list[ClusterProfile] = []

    for cid, grp in work.groupby("cluster"):
        sched_mean = float(grp["Days for shipment (scheduled)"].mean())
        qty_mean = float(grp["Order Item Quantity"].mean())
        sales_mean = float(grp["Sales"].mean())
        lat_mean = float(grp["Latitude"].mean())
        lon_mean = float(grp["Longitude"].mean())
        late_rate = float(grp[TARGET_COLUMN].mean())
        top_mode = str(grp["Shipping Mode"].mode().iloc[0])
        desc = describe_cluster_business_profile(sched_mean, qty_mean, lat_mean)
        profiles.append(
            ClusterProfile(
                cluster_id=int(cid),
                order_count=int(len(grp)),
                scheduled_days_mean=round(sched_mean, 2),
                quantity_mean=round(qty_mean, 2),
                sales_mean=round(sales_mean, 2),
                latitude_mean=round(lat_mean, 2),
                longitude_mean=round(lon_mean, 2),
                late_delivery_rate=round(late_rate, 4),
                top_shipping_mode=top_mode,
                business_description=desc,
            )
        )
    return profiles


def split_and_preprocess(
    df: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str], pd.DataFrame]:
    """Separa Train/Test (80/20, random_state=42) ANTES de ajustar escaladores e imputadores."""
    feature_cols = list(NUMERIC_FEATURES) + list(CATEGORICAL_FEATURES)
    validate_no_data_leakage(feature_cols)

    x_raw = df[feature_cols]
    y_raw = df[TARGET_COLUMN].to_numpy(dtype=int)

    x_train_df, x_test_df, y_train, y_test = train_test_split(
        x_raw,
        y_raw,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y_raw,
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                list(NUMERIC_FEATURES),
            ),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                list(CATEGORICAL_FEATURES),
            ),
        ]
    )

    x_train = preprocessor.fit_transform(x_train_df)
    x_test = preprocessor.transform(x_test_df)
    cat_names = list(
        preprocessor.named_transformers_["cat"].get_feature_names_out(list(CATEGORICAL_FEATURES))
    )
    feature_names = list(NUMERIC_FEATURES) + cat_names
    return x_train, x_test, y_train, y_test, feature_names, x_test_df


def evaluate_predictions(
    model_name: str, y_true: np.ndarray, y_pred: np.ndarray
) -> SupervisedModelMetrics:
    """Calcula accuracy, precisión, recall, F1 y matriz de confusión."""
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    matrix_tuple = (
        (int(cm[0, 0]), int(cm[0, 1])),
        (int(cm[1, 0]), int(cm[1, 1])),
    )
    return SupervisedModelMetrics(
        model_name=model_name,
        accuracy=round(float(accuracy_score(y_true, y_pred)), 4),
        precision=round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        recall=round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        f1=round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        confusion_matrix=matrix_tuple,
    )


def run_task_b_supervised(
    x_train: np.ndarray,
    x_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    feature_names: list[str],
    tree_max_depth: int = 5,
) -> tuple[list[SupervisedModelMetrics], list[tuple[str, float]], np.ndarray]:
    """Entrena Línea Base, LogisticRegression(balanced) y DecisionTree(max_depth=3..6)."""
    baseline_zero = DummyClassifier(strategy="constant", constant=0)
    baseline_zero.fit(x_train, y_train)
    pred_zero = baseline_zero.predict(x_test)

    baseline_maj = DummyClassifier(strategy="most_frequent", random_state=RANDOM_STATE)
    baseline_maj.fit(x_train, y_train)
    pred_maj = baseline_maj.predict(x_test)

    log_reg = LogisticRegression(class_weight="balanced", random_state=RANDOM_STATE, max_iter=1000)
    log_reg.fit(x_train, y_train)
    pred_lr = log_reg.predict(x_test)

    tree = DecisionTreeClassifier(max_depth=tree_max_depth, random_state=RANDOM_STATE)
    tree.fit(x_train, y_train)
    pred_tree = tree.predict(x_test)

    results = [
        evaluate_predictions("Baseline (sin alerta=0)", y_test, pred_zero),
        evaluate_predictions("Baseline (most_frequent)", y_test, pred_maj),
        evaluate_predictions("LogisticRegression (balanced)", y_test, pred_lr),
        evaluate_predictions(f"DecisionTree (max_depth={tree_max_depth})", y_test, pred_tree),
    ]

    importances = sorted(
        zip(feature_names, [float(v) for v in tree.feature_importances_], strict=False),
        key=lambda item: item[1],
        reverse=True,
    )
    return results, importances[:10], pred_tree


def run_task_c_error_analysis(
    x_test_df: pd.DataFrame,
    y_test: np.ndarray,
    y_pred: np.ndarray,
    segment_col: str = "Shipping Mode",
) -> list[SegmentRecall]:
    """Calcula el recall de retrasos desglosado por modo de envío o región (Tarea C)."""
    eval_df = x_test_df[[segment_col]].copy()
    eval_df["y_true"] = y_test
    eval_df["y_pred"] = y_pred

    segments: list[SegmentRecall] = []
    for seg_val, grp in eval_df.groupby(segment_col):
        rec = float(recall_score(grp["y_true"], grp["y_pred"], zero_division=0))
        late_rate = float(grp["y_true"].mean())
        segments.append(
            SegmentRecall(
                segment_type=segment_col,
                segment_value=str(seg_val),
                order_count=int(len(grp)),
                actual_late_rate=round(late_rate, 4),
                recall=round(rec, 4),
            )
        )
    return segments


def save_elbow_and_silhouette_plot(
    metrics: list[ClusterMetric], best_k: int, output_path: Path
) -> None:
    """Guarda el gráfico de método del codo y coeficiente de silueta de la Tarea A."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ks = [m.k for m in metrics]
    inertias = [m.inertia for m in metrics]
    silhouettes = [m.silhouette for m in metrics]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    ax1.plot(ks, inertias, marker="o", linewidth=2, color="#1f77b4")
    ax1.axvline(best_k, linestyle="--", color="#d62728", alpha=0.7, label=f"k={best_k}")
    ax1.set_title("Método del Codo (Inercia vs k)")
    ax1.set_xlabel("Número de clusters (k)")
    ax1.set_ylabel("Inercia (WCSS)")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    ax2.plot(ks, silhouettes, marker="s", linewidth=2, color="#2ca02c")
    ax2.axvline(best_k, linestyle="--", color="#d62728", alpha=0.7, label=f"k={best_k}")
    ax2.set_title("Coeficiente de Silueta vs k")
    ax2.set_xlabel("Número de clusters (k)")
    ax2.set_ylabel("Coeficiente de Silueta")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)


def save_confusion_matrix_plot(model_metrics: SupervisedModelMetrics, output_path: Path) -> None:
    """Guarda el gráfico de la matriz de confusión del mejor modelo de la Tarea B."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cm = np.array(model_metrics.confusion_matrix)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    fig.colorbar(im, ax=ax)

    labels = ["A tiempo (0)", "Retraso (1)"]
    ax.set_xticks([0, 1], labels=labels)
    ax.set_yticks([0, 1], labels=labels)
    ax.set_xlabel("Predicción del modelo")
    ax.set_ylabel("Valor real")
    ax.set_title(f"Matriz de Confusión — {model_metrics.model_name}")

    threshold = cm.max() / 2.0
    for i in range(2):
        for j in range(2):
            color = "white" if cm[i, j] > threshold else "black"
            ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center", color=color, fontsize=12)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
