"""src/domain/mantenimiento/costos.py — Supuesto de costos de errores y costo total para mantenimiento."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorCosts:
    """Costo hipotético de cada error: falla no detectada (FN) y revisión innecesaria (FP)."""

    false_negative: float
    false_positive: float

    def __post_init__(self) -> None:
        if self.false_negative < 0 or self.false_positive < 0:
            raise ValueError("Los costos no pueden ser negativos")


DEFAULT_COSTS: ErrorCosts = ErrorCosts(false_negative=100.0, false_positive=10.0)


def total_cost(false_negatives: int, false_positives: int, costs: ErrorCosts) -> float:
    """Costo total = FN * costo de falla no detectada + FP * costo de revisión innecesaria."""
    return false_negatives * costs.false_negative + false_positives * costs.false_positive
