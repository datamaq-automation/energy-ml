"""src/application/ventas/use_cases.py — Casos de uso: agrupar series (Tarea A) y pronosticar (Tareas B y C)."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.ventas.modelos import (
    FECHA_CORTE,
    K_ELEGIDO,
    PISTAS,
    VALORES_K,
    Agrupamiento,
    ErrorGrupo,
    ErrorMetodo,
    Pronosticos,
    Serie,
    errores_por_grupo,
    errores_por_metodo,
    validar_sin_fuga,
)
from src.domain.ventas.puertos import AgrupadorSeries, FuenteVentas, PronosticadorVentas


@dataclass(frozen=True)
class ResultadoPronostico:
    """Pronósticos del examen, error por método (B) y error por grupo (C)."""

    pronosticos: Pronosticos
    por_metodo: tuple[ErrorMetodo, ...]
    por_grupo: tuple[ErrorGrupo, ...]


class AgruparSeriesUseCase:
    """Tarea A: arma grupos de series (tienda, producto) con K-means."""

    def __init__(self, fuente: FuenteVentas, agrupador: AgrupadorSeries) -> None:
        self._fuente = fuente
        self._agrupador = agrupador

    def ejecutar(
        self, k_elegido: int = K_ELEGIDO, valores_k: tuple[int, ...] = VALORES_K
    ) -> Agrupamiento:
        """Evalúa cada k (codo y silueta) y asigna los grupos con el k elegido."""
        if k_elegido not in valores_k:
            raise ValueError(f"k={k_elegido} no está entre los valores evaluados {valores_k}.")
        return self._agrupador.agrupar(self._fuente.leer(), valores_k, k_elegido)


class PronosticarDemandaUseCase:
    """Tareas B y C: compara 'igual que ayer', regresión lineal y bosque aleatorio."""

    def __init__(self, fuente: FuenteVentas, pronosticador: PronosticadorVentas) -> None:
        self._fuente = fuente
        self._pronosticador = pronosticador

    def ejecutar(
        self,
        grupo_por_serie: dict[Serie, int],
        pistas: tuple[str, ...] = PISTAS,
        fecha_corte: str = FECHA_CORTE,
    ) -> ResultadoPronostico:
        """Verifica que no haya fuga, pronostica el examen y mide los errores."""
        validar_sin_fuga(pistas)
        pronosticos = self._pronosticador.pronosticar(self._fuente.leer(), pistas, fecha_corte)
        return ResultadoPronostico(
            pronosticos=pronosticos,
            por_metodo=tuple(errores_por_metodo(pronosticos)),
            por_grupo=tuple(errores_por_grupo(pronosticos, grupo_por_serie)),
        )
