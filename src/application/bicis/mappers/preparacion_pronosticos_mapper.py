"""src/application/bicis/mappers/preparacion_pronosticos_mapper.py — Resultado → DTO."""

from src.application.bicis.dtos.preparar_pronosticos_response import (
    PrepararPronosticosResponse,
)
from src.domain.bicis.value_objects import ResultadoPreparacionPronosticos


class PreparacionPronosticosMapper:
    """Convierte la preparación del dominio al contrato de salida de la aplicación."""

    @staticmethod
    def a_response(
        resultado: ResultadoPreparacionPronosticos,
    ) -> PrepararPronosticosResponse:
        """Copia las muestras y las fechas excluidas a un DTO inmutable."""
        return PrepararPronosticosResponse(
            muestras=resultado.muestras,
            dias_faltantes=resultado.dias_faltantes,
            dias_sin_rezagos=resultado.dias_sin_rezagos,
        )
