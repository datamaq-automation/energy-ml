"""src/application/sibo/politica_modelo.py — Política configurable del modelo híbrido."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PoliticaModelo:
    """Decisión de modelado: mezcla modelo/heurística y percentiles de la banda.

    Los valores por defecto son un punto de partida explícito, no una elección
    validada con datos reales. Cambiarlos no requiere tocar la infraestructura.
    """

    peso_modelo: float = 0.7
    peso_heuristica: float = 0.3
    percentil_bajo: float = 10.0
    percentil_alto: float = 90.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.peso_modelo <= 1.0:
            raise ValueError("peso_modelo debe estar entre 0 y 1")
        if not 0.0 <= self.peso_heuristica <= 1.0:
            raise ValueError("peso_heuristica debe estar entre 0 y 1")
        if abs(self.peso_modelo + self.peso_heuristica - 1.0) > 1e-9:
            raise ValueError("Los pesos del modelo y la heurística deben sumar 1")
        if not 0.0 <= self.percentil_bajo < self.percentil_alto <= 100.0:
            raise ValueError("Los percentiles deben cumplir 0 <= bajo < alto <= 100")
