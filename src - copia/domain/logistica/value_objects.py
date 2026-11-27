"""src/domain/logistica/value_objects.py — Vocabulario y resultados inmutables del caso de retrasos."""

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
