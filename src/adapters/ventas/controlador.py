"""src/adapters/ventas/controlador.py — Controlador: corre las Tareas A, B y C en orden y arma el reporte."""

from __future__ import annotations

from dataclasses import dataclass

from src.adapters.ventas.presentador import presentar_agrupamiento, presentar_pronostico
from src.application.ventas.use_cases import (
    AgruparSeriesUseCase,
    PronosticarDemandaUseCase,
    ResultadoPronostico,
)
from src.domain.ventas.modelos import Agrupamiento


@dataclass(frozen=True)
class ReporteVentas:
    """Resultados de las tres tareas y sus renglones de texto."""

    agrupamiento: Agrupamiento
    pronostico: ResultadoPronostico
    renglones: tuple[str, ...]


class ControladorVentas:
    """Primero agrupa (A); con esos grupos pronostica (B) y mide el error por grupo (C)."""

    def __init__(
        self, agrupar: AgruparSeriesUseCase, pronosticar: PronosticarDemandaUseCase
    ) -> None:
        self._agrupar = agrupar
        self._pronosticar = pronosticar

    def analizar(self, k_elegido: int) -> ReporteVentas:
        """Ejecuta las tres tareas y devuelve el reporte."""
        agrupamiento = self._agrupar.ejecutar(k_elegido=k_elegido)
        pronostico = self._pronosticar.ejecutar(agrupamiento.grupo_por_serie)
        renglones = presentar_agrupamiento(agrupamiento) + presentar_pronostico(pronostico)
        return ReporteVentas(agrupamiento, pronostico, tuple(renglones))
