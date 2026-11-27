"""src/domain/crecidas/modelos.py — Entidades del dominio de crecidas (sin dependencias externas)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Escenario(str, Enum):
    """Escenario de nivel de río, de menor a mayor riesgo."""

    NORMAL = "normal"
    VIGILANCIA = "vigilancia"
    ALERTA = "alerta"
    CRECIDA = "crecida"


@dataclass(frozen=True)
class Umbrales:
    """Niveles de río (en metros sobre el cero de la escala) que delimitan los escenarios.

    Invariante: vigilancia < alerta < crecida.
    """

    vigilancia_m: float
    alerta_m: float
    crecida_m: float

    def __post_init__(self) -> None:
        if not (self.vigilancia_m < self.alerta_m < self.crecida_m):
            raise ValueError(
                "Los umbrales deben cumplir vigilancia < alerta < crecida "
                f"(recibido: {self.vigilancia_m}, {self.alerta_m}, {self.crecida_m})"
            )


@dataclass(frozen=True)
class AlertaTemprana:
    """Alerta emitida cuando el nivel previsto alcanza alerta o crecida.

    Guarda los datos que la dispararon para que sea auditable.
    """

    escenario: Escenario
    nivel_previsto_m: float
    horizonte_horas: int
    umbral_disparado_m: float


@dataclass(frozen=True)
class NivelRio:
    """Una observación de altura hidrométrica (metros) en un instante dado."""

    instante: datetime
    nivel_m: float


@dataclass(frozen=True)
class NivelesOficiales:
    """Niveles oficiales de Prefectura Naval para una estación (metros sobre su cero de escala).

    Prefectura define solo alerta y evacuación; no define vigilancia.
    """

    alerta_m: float
    evacuacion_m: float
    aguas_bajas_m: float

    def a_umbrales(self, vigilancia_m: float) -> Umbrales:
        """Mapea a Umbrales: alerta -> alerta, evacuación -> crecida.

        La vigilancia no es oficial: la aporta quien llama (sección 9.1 de la spec).
        """
        return Umbrales(
            vigilancia_m=vigilancia_m,
            alerta_m=self.alerta_m,
            crecida_m=self.evacuacion_m,
        )


# Fuente: reporte "Registro del estado de los ríos" de Prefectura Naval Argentina
# (https://contenidosweb.prefecturanaval.gob.ar/alturas/pdf.php), confirmado en la API del INA
# (estación Tigre, id_externo 430). Río Luján.
NIVELES_OFICIALES_TIGRE = NivelesOficiales(
    alerta_m=3.30,
    evacuacion_m=3.80,
    aguas_bajas_m=0.30,
)
