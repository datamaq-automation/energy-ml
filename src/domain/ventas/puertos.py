"""src/domain/ventas/puertos.py — Puertos (contratos) que el pronóstico de ventas necesita de afuera."""

from __future__ import annotations

from typing import Any, Protocol

from src.domain.ventas.modelos import Agrupamiento, Pronosticos


class FuenteVentas(Protocol):
    """Entrega la tabla de ventas diarias (columnas date, store, item, sales)."""

    def leer(self) -> Any: ...


class AgrupadorSeries(Protocol):
    """Agrupa las series (tienda, producto) según su perfil de ventas (Tarea A)."""

    def agrupar(self, ventas: Any, valores_k: tuple[int, ...], k_elegido: int) -> Agrupamiento: ...


class PronosticadorVentas(Protocol):
    """Aprende con el pasado y pronostica el examen con cada método (Tarea B)."""

    def pronosticar(
        self, ventas: Any, pistas: tuple[str, ...], fecha_corte: str
    ) -> Pronosticos: ...
