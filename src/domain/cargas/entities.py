"""src/domain/cargas/entities.py — Entidades del dominio de identificación de cargas (NILM)."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Medicion:
    """Potencia activa total de un medidor en un instante, siempre en kW."""

    instante: datetime
    potencia_kw: float


@dataclass(frozen=True)
class EventoCarga:
    """Cambio de estado: salto de potencia entre dos mediciones consecutivas."""

    instante: datetime
    delta_kw: float

    @property
    def es_encendido(self) -> bool:
        return self.delta_kw > 0


@dataclass(frozen=True)
class Carga:
    """Carga candidata: grupo de eventos con magnitud similar."""

    potencia_tipica_kw: float
    encendidos: int
    apagados: int

    @property
    def ciclos(self) -> int:
        return min(self.encendidos, self.apagados)

    def es_on_off(self, balance_minimo: float) -> bool:
        """Una carga ON/OFF real se enciende y se apaga una cantidad parecida de veces."""
        mayor = max(self.encendidos, self.apagados)
        return mayor > 0 and self.ciclos / mayor >= balance_minimo
