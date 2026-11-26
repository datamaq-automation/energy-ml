"""src/domain/bicis/exceptions.py — Errores de negocio del pronóstico de viajes."""

from __future__ import annotations


class ErrorPronosticos(ValueError):
    """Error base del bounded context de bicicletas públicas."""


class PeriodoPronosticoInvalidoError(ErrorPronosticos):
    """El período solicitado no puede evaluarse en el orden indicado."""


class MuestrasInsuficientesError(ErrorPronosticos):
    """Faltan muestras utilizables para entrenamiento o prueba."""
