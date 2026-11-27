"""src/domain/medioambiente/entities.py — Informe de episodios de CO (entidad con identidad)."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.medioambiente.events import Tarea, TareaCompletada
from src.domain.medioambiente.services import elegir_mejor_k, elegir_mejor_modelo
from src.domain.medioambiente.value_objects import (
    CambioDistribucion,
    DiagnosticoK,
    MetricasModelo,
    Particion,
    PerfilGrupo,
)


@dataclass
class InformeEpisodiosCO:
    """Resultados de las Tareas A, B y C; se identifica por `id` (una corrida del análisis)."""

    id: str
    filas_cargadas: int
    diagnosticos: list[DiagnosticoK] = field(default_factory=list)
    grupos: list[PerfilGrupo] = field(default_factory=list)
    metricas: list[MetricasModelo] = field(default_factory=list)
    cambios: list[CambioDistribucion] = field(default_factory=list)
    eventos: list[TareaCompletada] = field(default_factory=list)

    def registrar_agrupamiento(
        self, diagnosticos: list[DiagnosticoK], grupos: list[PerfilGrupo]
    ) -> None:
        """Tarea A: guarda el diagnóstico de k y los perfiles de los grupos."""
        self.diagnosticos = diagnosticos
        self.grupos = grupos
        self.eventos.append(
            TareaCompletada(Tarea.A, f"mejor k por silueta = {self.mejor_k}, {len(grupos)} grupos")
        )

    def registrar_metricas(self, metricas: list[MetricasModelo]) -> None:
        """Tareas B y C: agrega las métricas de una partición."""
        self.metricas.extend(metricas)
        if any(metrica.particion is Particion.ALEATORIA for metrica in metricas):
            self.eventos.append(
                TareaCompletada(Tarea.B, f"{len(metricas)} modelos evaluados (split aleatorio)")
            )

    def registrar_cambios(self, cambios: list[CambioDistribucion]) -> None:
        """Tarea C: guarda la comparación de distribuciones train/test temporal."""
        self.cambios = cambios
        self.eventos.append(
            TareaCompletada(
                Tarea.C,
                f"mejor modelo temporal = {self.mejor_modelo_temporal.modelo}, "
                f"features con cambio = {self.features_con_cambio or 'ninguna'}",
            )
        )

    @property
    def mejor_k(self) -> int:
        """k elegido por silueta."""
        return elegir_mejor_k(self.diagnosticos)

    @property
    def mejor_modelo_temporal(self) -> MetricasModelo:
        """Modelo con mayor F1 en el split temporal (el único compatible con un aviso real)."""
        return elegir_mejor_modelo(m for m in self.metricas if m.particion is Particion.TEMPORAL)

    @property
    def features_con_cambio(self) -> list[str]:
        """Features cuya media se desplazó más que el umbral entre train y test."""
        return [cambio.feature for cambio in self.cambios if cambio.cambio]
