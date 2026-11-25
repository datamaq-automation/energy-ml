"""src/domain/medioambiente/exceptions.py — Errores de negocio del caso de episodios de CO.

Heredan de ValueError: quien ya capturaba ValueError sigue funcionando.
"""

from __future__ import annotations


class ErrorMedioambiente(ValueError):
    """Raíz de los errores del bounded context medioambiente."""


class ColumnasFaltantesError(ErrorMedioambiente):
    """La tabla no trae las columnas que necesita el paso siguiente."""

    def __init__(self, mensaje: str, columnas: list[str]) -> None:
        self.columnas = columnas
        super().__init__(mensaje)


class FugaDeDatosError(ErrorMedioambiente):
    """Una feature sale de la misma hora que se quiere predecir o genera la etiqueta."""

    def __init__(self, columnas: list[str]) -> None:
        self.columnas = columnas
        super().__init__(f"Fuga de datos: {columnas} no pueden usarse como entrada.")


class SinDiagnosticosError(ErrorMedioambiente):
    """No hay diagnósticos de K-means para elegir k."""


class ProporcionInvalidaError(ErrorMedioambiente):
    """La proporción de train no está en el intervalo abierto (0, 1)."""
