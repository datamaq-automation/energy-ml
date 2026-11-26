"""src/application/bicis/dtos/preparar_pronosticos_request.py — Entrada para preparar muestras."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator


class PrepararPronosticosRequest(BaseModel):
    """Intervalo inclusivo de fechas que se desea preparar."""

    model_config = ConfigDict(frozen=True)

    desde: date
    hasta: date

    @model_validator(mode="after")
    def validar_intervalo(self) -> PrepararPronosticosRequest:
        """Valida el rango al recibir la entrada, antes de consultar el repositorio."""
        if self.desde > self.hasta:
            raise ValueError("La fecha inicial no puede ser posterior a la fecha final.")
        return self
