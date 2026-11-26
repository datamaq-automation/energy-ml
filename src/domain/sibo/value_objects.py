"""src/domain/sibo/value_objects.py — Política de modelado y constantes nutricionales del dominio."""

from __future__ import annotations

from dataclasses import dataclass

FODMAP_VALOR: dict[str, float] = {"bajo": 0.1, "medio": 0.5, "alto": 0.9}
VENTANA_DIGESTION_HORAS: float = 8.0
HORA_PICO_HORAS: float = 2.0


@dataclass(frozen=True)
class PoliticaModelo:
    """Mezcla modelo/heurística y percentiles de la banda de gases.

    Son reglas del problema, no detalles de sklearn: la infraestructura las recibe.
    Los valores por defecto son un punto de partida, no una decisión validada con
    datos reales, y pueden ajustarse sin tocar el modelo.
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
