"""src/domain/logistica/models.py — Modelos de dominio y reglas anti-fuga de datos para logística."""

from __future__ import annotations

from dataclasses import dataclass

TARGET_COLUMN: str = "Late_delivery_risk"

FORBIDDEN_COLUMNS: tuple[str, ...] = (
    "Days for shipping (real)",
    "Delivery Status",
    "shipping date (DateOrders)",
    "Late_delivery_risk",
    "Order Status",
)

KMEANS_FEATURES: tuple[str, ...] = (
    "Days for shipment (scheduled)",
    "Order Item Quantity",
    "Sales",
    "Latitude",
    "Longitude",
)

NUMERIC_FEATURES: tuple[str, ...] = (
    "Days for shipment (scheduled)",
    "Order Item Quantity",
    "Sales",
    "Order Item Discount Rate",
    "Latitude",
    "Longitude",
    "order_month",
    "order_dayofweek",
    "order_hour",
)

CATEGORICAL_FEATURES: tuple[str, ...] = (
    "Shipping Mode",
    "Market",
    "Order Region",
    "Customer Segment",
)


@dataclass(frozen=True)
class ClusterMetric:
    """Métricas de evaluación de K-Means para un valor dado de k."""

    k: int
    inertia: float
    silhouette: float


@dataclass(frozen=True)
class ClusterProfile:
    """Perfil operativo y proporción de retrasos (post-hoc) de un cluster."""

    cluster_id: int
    order_count: int
    scheduled_days_mean: float
    quantity_mean: float
    sales_mean: float
    latitude_mean: float
    longitude_mean: float
    late_delivery_rate: float
    top_shipping_mode: str
    business_description: str


@dataclass(frozen=True)
class SupervisedModelMetrics:
    """Métricas de clasificación supervisada sobre el conjunto de evaluación (test)."""

    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    confusion_matrix: tuple[tuple[int, int], tuple[int, int]]


@dataclass(frozen=True)
class SegmentRecall:
    """Análisis de errores (Tarea C): recall y tasa real de retrasos por segmento."""

    segment_type: str
    segment_value: str
    order_count: int
    actual_late_rate: float
    recall: float


def validate_no_data_leakage(feature_columns: list[str] | tuple[str, ...]) -> None:
    """Verifica que ninguna variable prohibida (fuga de datos) esté presente en X."""
    forbidden_set = {col.lower().strip() for col in FORBIDDEN_COLUMNS}
    leaked = [col for col in feature_columns if col.lower().strip() in forbidden_set]
    if leaked:
        raise ValueError(f"Data leakage detectado: las columnas {leaked} están prohibidas en X.")


def describe_cluster_business_profile(
    scheduled_days_mean: float,
    quantity_mean: float,
    latitude_mean: float,
) -> str:
    """Genera una descripción en lenguaje de negocio según los centroides del grupo."""
    hub = "Hub Caribe (PR)" if latitude_mean < 25.0 else "Hub EE.UU. Continental"
    if quantity_mean >= 3.5:
        return f"Pedidos mayoristas de alto volumen y alto ticket ({hub})"
    if scheduled_days_mean <= 2.0:
        return f"Envíos rápidos/urgentes (1-2 días programados) desde {hub}"
    return f"Envíos estándar (4 días programados) de bajo volumen desde {hub}"
