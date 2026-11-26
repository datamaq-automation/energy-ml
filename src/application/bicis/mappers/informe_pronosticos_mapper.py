"""src/application/bicis/mappers/informe_pronosticos_mapper.py — Entidad → DTO de salida."""

from src.application.bicis.dtos.evaluar_pronosticos_response import (
    EvaluarPronosticosResponse,
)
from src.domain.bicis.entities import InformePronosticos


class InformePronosticosMapper:
    """Convierte el informe del dominio al contrato de respuesta de la aplicación."""

    @staticmethod
    def a_response(informe: InformePronosticos) -> EvaluarPronosticosResponse:
        """Copia métricas, cobertura y eventos a un DTO inmutable."""
        resultado = informe.evaluacion
        return EvaluarPronosticosResponse(
            id_informe=informe.id,
            linea_base=resultado.linea_base,
            bosque_aleatorio=resultado.bosque_aleatorio,
            dias_entrenamiento=resultado.dias_entrenamiento,
            dias_prueba=resultado.dias_prueba,
            dias_faltantes=informe.dias_faltantes,
            dias_sin_rezagos=informe.dias_sin_rezagos,
            eventos=tuple(
                f"Pronósticos evaluados del {evento.desde} al {evento.hasta}: "
                f"{evento.dias_prueba} días de prueba"
                for evento in informe.eventos
            ),
        )
