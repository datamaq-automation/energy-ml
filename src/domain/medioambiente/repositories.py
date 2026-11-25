"""src/domain/medioambiente/repositories.py — Puertos: de dónde salen los datos y quién modela.

El dominio no conoce pandas: la tabla de mediciones es un tipo opaco (`Datos`)
que solo el adaptador concreto sabe manejar.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

from src.domain.medioambiente.value_objects import (
    CambioDistribucion,
    DiagnosticoK,
    MetricasModelo,
    Particion,
    PerfilGrupo,
)

DatosCo = TypeVar("DatosCo", covariant=True)
Datos = TypeVar("Datos")


class RepositorioCalidadAire(Protocol[DatosCo]):
    """Fuente de las mediciones horarias crudas de Air Quality (UCI #360)."""

    def cargar(self) -> DatosCo:
        """Devuelve la tabla cruda, con los faltantes ya marcados como tales."""
        ...


class ModeladorEpisodios(Protocol[Datos]):
    """Motor de aprendizaje automático para las Tareas A, B y C."""

    def contar_filas(self, crudo: Datos) -> int:
        """Cantidad de mediciones horarias cargadas."""
        ...

    def diagnosticar_k(self, crudo: Datos) -> list[DiagnosticoK]:
        """Tarea A: inercia y silueta de K-means para cada k candidato."""
        ...

    def perfilar_grupos(self, crudo: Datos, k: int) -> list[PerfilGrupo]:
        """Tarea A: agrupa con k clusters y describe cada grupo."""
        ...

    def preparar(self, crudo: Datos) -> Datos:
        """Agrega features anticipables y la etiqueta `episodio`."""
        ...

    def evaluar(self, datos: Datos, particion: Particion) -> list[MetricasModelo]:
        """Tareas B y C: entrena con train y mide sobre test de la partición pedida."""
        ...

    def detectar_cambios(self, datos: Datos) -> list[CambioDistribucion]:
        """Tarea C: compara las features entre train y test temporales."""
        ...

    def graficar_diagnosticos(self, diagnosticos: list[DiagnosticoK], destino: str) -> list[str]:
        """Guarda los gráficos de codo y silueta; devuelve las rutas creadas."""
        ...
