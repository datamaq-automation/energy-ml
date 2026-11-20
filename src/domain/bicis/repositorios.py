"""src/domain/bicis/repositorios.py — Puerto para obtener la serie diaria."""

from datetime import date
from typing import Protocol

from src.domain.bicis.modelos import SerieDiariaViajes


class RepositorioSerieDiaria(Protocol):
    """Fuente de totales diarios para un intervalo de fechas."""

    def obtener(self, desde: date, hasta: date) -> SerieDiariaViajes:
        """Retorna los días disponibles sin completar ausencias con ceros."""
        ...
