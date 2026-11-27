"""src/domain/logistica/exceptions.py — Errores de negocio del caso de retrasos logísticos.

Heredan de ValueError: quien ya capturaba ValueError sigue funcionando.
"""

from __future__ import annotations


class ErrorLogistica(ValueError):
    """Raíz de los errores del bounded context logística."""


class FugaDeDatosError(ErrorLogistica):
    """Una variable que no existe al momento de despachar el pedido entró como feature."""

    def __init__(self, columnas: list[str]) -> None:
        self.columnas = columnas
        super().__init__(f"Data leakage detectado: las columnas {columnas} están prohibidas en X.")


class SinResultadosError(ErrorLogistica):
    """Se pidió un resultado de una tarea que todavía no se ejecutó."""
