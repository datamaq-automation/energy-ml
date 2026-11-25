"""src/application/logistica/mappers/informe_retrasos_mapper.py — Entidad → DTO de respuesta."""

from __future__ import annotations

from src.application.logistica.dtos.analizar_retrasos_response import (
    AnalizarRetrasosResponse,
    MetricasModeloDTO,
    PerfilGrupoDTO,
    SegmentoDTO,
)
from src.domain.logistica.entities import InformeRetrasos


class InformeRetrasosMapper:
    """Traduce el informe del dominio al contrato de salida de la aplicación."""

    @staticmethod
    def a_response(informe: InformeRetrasos, graficos: list[str]) -> AnalizarRetrasosResponse:
        """Arma la respuesta con las cinco variables más importantes del árbol."""
        return AnalizarRetrasosResponse(
            id_informe=informe.id,
            pedidos=informe.pedidos,
            ks_evaluados=[metrica.k for metrica in informe.metricas_k],
            perfiles=[
                PerfilGrupoDTO(
                    cluster_id=p.cluster_id,
                    order_count=p.order_count,
                    business_description=p.business_description,
                    late_delivery_rate=p.late_delivery_rate,
                )
                for p in informe.perfiles
            ],
            modelos=[
                MetricasModeloDTO(
                    model_name=m.model_name,
                    accuracy=m.accuracy,
                    precision=m.precision,
                    recall=m.recall,
                    f1=m.f1,
                    confusion_matrix=[list(fila) for fila in m.confusion_matrix],
                )
                for m in informe.modelos
            ],
            importancias=informe.importancias[:5],
            segmentos=[SegmentoDTO(**vars(segmento)) for segmento in informe.segmentos],
            graficos=graficos,
            eventos=[f"Tarea {e.tarea.value}: {e.resumen}" for e in informe.eventos],
        )
