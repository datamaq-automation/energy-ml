"""src/domain/logistica/entities.py — Informe de retrasos logísticos (entidad con identidad)."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.logistica.events import Tarea, TareaCompletada
from src.domain.logistica.exceptions import SinResultadosError
from src.domain.logistica.value_objects import (
    ClusterMetric,
    ClusterProfile,
    SegmentRecall,
    SupervisedModelMetrics,
)


@dataclass
class InformeRetrasos:
    """Resultados de las Tareas A, B y C; se identifica por `id` (una corrida del análisis)."""

    id: str
    pedidos: int
    metricas_k: list[ClusterMetric] = field(default_factory=list)
    perfiles: list[ClusterProfile] = field(default_factory=list)
    modelos: list[SupervisedModelMetrics] = field(default_factory=list)
    importancias: list[tuple[str, float]] = field(default_factory=list)
    segmentos: list[SegmentRecall] = field(default_factory=list)
    eventos: list[TareaCompletada] = field(default_factory=list)

    def registrar_agrupamiento(
        self, metricas_k: list[ClusterMetric], perfiles: list[ClusterProfile]
    ) -> None:
        """Tarea A: diagnóstico de k y perfil de cada grupo."""
        self.metricas_k = metricas_k
        self.perfiles = perfiles
        self.eventos.append(TareaCompletada(Tarea.A, f"{len(perfiles)} grupos perfilados"))

    def registrar_clasificacion(
        self,
        modelos: list[SupervisedModelMetrics],
        importancias: list[tuple[str, float]],
        segmentos: list[SegmentRecall],
    ) -> None:
        """Tareas B y C: métricas por modelo y recall del árbol desglosado por segmento."""
        self.modelos = modelos
        self.importancias = importancias
        self.segmentos = segmentos
        self.eventos.append(
            TareaCompletada(
                Tarea.B, f"{len(modelos)} modelos; final = {self.modelo_final.model_name}"
            )
        )
        self.eventos.append(TareaCompletada(Tarea.C, f"{len(segmentos)} segmentos analizados"))

    @property
    def modelo_final(self) -> SupervisedModelMetrics:
        """El árbol de decisión: último modelo evaluado y el que se desglosa en la Tarea C."""
        if not self.modelos:
            raise SinResultadosError("La Tarea B todavía no registró modelos.")
        return self.modelos[-1]
