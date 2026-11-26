"""src/domain/residuos/exceptions.py — Errores de negocio del pronóstico de residuos.

Heredan de ValueError: quien ya capturaba ValueError sigue funcionando.
"""

from __future__ import annotations


class ErrorResiduos(ValueError):
    """Raíz de los errores del bounded context residuos."""


class DatosInvalidosError(ErrorResiduos):
    """El CSV de la ciudad no cumple el contrato (columnas, rangos, meses completos)."""


class SerieCortaError(ErrorResiduos):
    """La serie mensual no alcanza para entrenar o para la validación temporal pedida."""


class ModeloDesconocidoError(ErrorResiduos):
    """Se pidió un modelo que no está entre los comparados."""

    def __init__(self, modelo: str) -> None:
        self.modelo = modelo
        super().__init__(f"Modelo desconocido: {modelo}")
