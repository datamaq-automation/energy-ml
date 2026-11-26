"""src/application/residuos/mappers/informe_residuos_mapper.py — Entidad → DTO de respuesta."""

from __future__ import annotations

from src.application.residuos.dtos.pronosticar_residuos_response import (
    MetricaValidacionDTO,
    PronosticarResiduosResponse,
    PronosticoDTO,
)
from src.domain.residuos.entities import InformeResiduos


class InformeResiduosMapper:
    """Traduce el informe del dominio al contrato de salida de la aplicación."""

    @staticmethod
    def a_response(informe: InformeResiduos, archivos: list[str]) -> PronosticarResiduosResponse:
        """Arma la respuesta con el rango de la serie y el modelo de menor MAE."""
        return PronosticarResiduosResponse(
            id_informe=informe.id,
            meses=len(informe.serie),
            primer_mes=informe.serie[0].mes,
            ultimo_mes=informe.serie[-1].mes,
            metricas=[MetricaValidacionDTO(**vars(m)) for m in informe.metricas],
            pronosticos=[PronosticoDTO(**vars(p)) for p in informe.pronosticos],
            mejor_modelo=informe.mejor_modelo.modelo,
            archivos=archivos,
            eventos=[f"{e.etapa.value}: {e.resumen}" for e in informe.eventos],
        )
