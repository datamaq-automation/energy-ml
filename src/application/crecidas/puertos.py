"""src/application/crecidas/puertos.py"""

from typing import Protocol


class PronosticadorNivelPort(Protocol):
    """Contrato que debe cumplir un predictor de niveles del río."""

    def entrenar(
        self,
        variables: list[list[float]],
        objetivos: list[float],
    ) -> None:
        """Entrena el predictor con datos históricos."""
        ...

    def predecir(
        self,
        variables: list[list[float]],
    ) -> list[float]:
        """Devuelve los niveles pronosticados."""
        ...
