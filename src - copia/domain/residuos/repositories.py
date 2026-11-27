"""src/domain/residuos/repositories.py — Puertos: registros de la ciudad y motor de pronóstico.

El dominio no conoce pandas: los registros crudos son un tipo opaco que solo
el adaptador concreto sabe manejar.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

from src.domain.residuos.value_objects import MetricaValidacion, Pronostico, TotalMensual

DatosCo = TypeVar("DatosCo", covariant=True)
DatosContra = TypeVar("DatosContra", contravariant=True)


class RepositorioResiduos(Protocol[DatosCo]):
    """Lee los registros de la ciudad y guarda los resultados del análisis."""

    def cargar(self) -> DatosCo:
        """Devuelve el total mensual de la ciudad, ya validado (columnas, rangos, meses)."""
        ...

    def guardar(
        self,
        serie: list[TotalMensual],
        metricas: list[MetricaValidacion],
        pronosticos: list[Pronostico],
    ) -> list[str]:
        """Persiste los tres resultados; devuelve las rutas escritas."""
        ...


class PronosticadorResiduos(Protocol[DatosContra]):
    """Motor de aprendizaje automático: serie, validación temporal y pronóstico."""

    def serie_mensual(self, datos: DatosContra) -> list[TotalMensual]:
        """Un total por mes para toda la ciudad."""
        ...

    def validar(self, datos: DatosContra) -> list[MetricaValidacion]:
        """MAE y RMSE de cada modelo en el último año, por horizonte y en bloque."""
        ...

    def pronosticar(self, datos: DatosContra) -> list[Pronostico]:
        """Pronósticos de cada modelo para los meses siguientes al último observado."""
        ...
