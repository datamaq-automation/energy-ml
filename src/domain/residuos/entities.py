"""src/domain/residuos/entities.py — Informe del pronóstico de residuos (entidad con identidad)."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.residuos.events import Etapa, EtapaCompletada
from src.domain.residuos.services import elegir_mejor_modelo
from src.domain.residuos.value_objects import MetricaValidacion, Pronostico, TotalMensual


@dataclass
class InformeResiduos:
    """Serie, validación y pronóstico; se identifica por `id` (una corrida del análisis)."""

    id: str
    serie: list[TotalMensual] = field(default_factory=list)
    metricas: list[MetricaValidacion] = field(default_factory=list)
    pronosticos: list[Pronostico] = field(default_factory=list)
    eventos: list[EtapaCompletada] = field(default_factory=list)

    def registrar_serie(self, serie: list[TotalMensual]) -> None:
        """Guarda la serie mensual validada."""
        self.serie = serie
        self.eventos.append(
            EtapaCompletada(Etapa.SERIE, f"{len(serie)} meses, de {serie[0].mes} a {serie[-1].mes}")
        )

    def registrar_validacion(self, metricas: list[MetricaValidacion]) -> None:
        """Guarda MAE y RMSE por modelo y horizonte."""
        self.metricas = metricas
        self.eventos.append(
            EtapaCompletada(Etapa.VALIDACION, f"menor MAE: {self.mejor_modelo.modelo}")
        )

    def registrar_pronosticos(self, pronosticos: list[Pronostico]) -> None:
        """Guarda los pronósticos posteriores al último mes disponible."""
        self.pronosticos = pronosticos
        meses = sorted({p.mes for p in pronosticos})
        self.eventos.append(EtapaCompletada(Etapa.PRONOSTICO, f"meses {', '.join(meses)}"))

    @property
    def mejor_modelo(self) -> MetricaValidacion:
        """Modelo con menor MAE en el bloque completo de la validación."""
        return elegir_mejor_modelo(self.metricas)
