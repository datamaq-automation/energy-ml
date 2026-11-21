"""src/domain/educacion/puertos.py — Puertos (contratos) que el caso educacion necesita de afuera."""

from __future__ import annotations

from typing import Any, Protocol


class FuenteEstudiantes(Protocol):
    """Entrega el dataset de estudiantes completo (395 filas, separador ';')."""

    def leer(self) -> Any: ...


class AgrupadorEstudiantes(Protocol):
    """Tarea A: diagnostica cada k (codo + silueta) y asigna grupos con el k elegido."""

    def diagnosticos(self, features: Any) -> tuple[list[int], list[float], list[float]]: ...

    def agrupar(self, features: Any, k: int) -> Any: ...


class EntrenadorRiesgo(Protocol):
    """Tarea B: ajusta los modelos supervisados y devuelve cada modelo ya entrenado."""

    def entrenar(self, x_train: Any, y_train: Any) -> dict[str, Any]: ...


class GraficadorGrupos(Protocol):
    """Muestra los gráficos de codo y silueta en pantalla (sin guardar archivos)."""

    def mostrar_codo_silueta(
        self, k_values: list[int], inertias: list[float], silhouettes: list[float]
    ) -> None: ...


class Bitacora(Protocol):
    """Registro de lo que hace el proceso (solo info, warning y error)."""

    def info(self, msg: str, *args: object) -> None: ...

    def warning(self, msg: str, *args: object) -> None: ...

    def error(self, msg: str, *args: object) -> None: ...
