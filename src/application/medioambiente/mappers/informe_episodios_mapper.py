"""src/application/medioambiente/mappers/informe_episodios_mapper.py — Entidad → DTO de respuesta."""

from __future__ import annotations

from src.application.medioambiente.dtos.analizar_episodios_response import (
    AnalizarEpisodiosResponse,
    CambioDistribucionDTO,
    DiagnosticoKDTO,
    MetricasModeloDTO,
    PerfilGrupoDTO,
)
from src.domain.medioambiente.entities import InformeEpisodiosCO
from src.domain.medioambiente.value_objects import MatrizConfusion, MetricasModelo


class InformeEpisodiosMapper:
    """Traduce el informe del dominio al contrato de salida de la aplicación."""

    @staticmethod
    def a_response(informe: InformeEpisodiosCO, graficos: list[str]) -> AnalizarEpisodiosResponse:
        """Arma la respuesta; la matriz es la del mejor modelo del split temporal."""
        mejor = informe.mejor_modelo_temporal
        return AnalizarEpisodiosResponse(
            id_informe=informe.id,
            filas_cargadas=informe.filas_cargadas,
            mejor_k=informe.mejor_k,
            diagnosticos=[
                DiagnosticoKDTO(k=d.k, inercia=d.inercia, silueta=d.silueta)
                for d in informe.diagnosticos
            ],
            grupos=[PerfilGrupoDTO(**vars(grupo)) for grupo in informe.grupos],
            metricas=[InformeEpisodiosMapper._metricas(m) for m in informe.metricas],
            mejor_modelo=mejor.modelo,
            matriz_confusion=InformeEpisodiosMapper._matriz(mejor.matriz),
            cambios=[CambioDistribucionDTO(**vars(cambio)) for cambio in informe.cambios],
            features_con_cambio=informe.features_con_cambio,
            graficos=graficos,
            eventos=[f"Tarea {e.tarea.value}: {e.resumen}" for e in informe.eventos],
        )

    @staticmethod
    def _metricas(metricas: MetricasModelo) -> MetricasModeloDTO:
        return MetricasModeloDTO(
            modelo=metricas.modelo,
            split=metricas.particion.value,
            accuracy=metricas.accuracy,
            precision=metricas.precision,
            recall=metricas.recall,
            f1=metricas.f1,
        )

    @staticmethod
    def _matriz(matriz: MatrizConfusion) -> list[list[int]]:
        """Formato [[TN, FP], [FN, TP]]."""
        return [
            [matriz.verdaderos_negativos, matriz.falsos_positivos],
            [matriz.falsos_negativos, matriz.verdaderos_positivos],
        ]
