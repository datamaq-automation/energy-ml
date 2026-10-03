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


@dataclass(frozen=True)
class EstimacionUmbral:
    """Umbral |ΔP| que mejor separa el ruido de los eventos (método de Otsu).

    separacion (η, entre 0 y 1) mide qué tan claras son las dos montañas del histograma:
    ~0,7 es lo que da una sola montaña (no hay nada que separar); cerca de 1, un valle limpio.
    """

    umbral_kw: float
    separacion: float

    def es_confiable(self, separacion_minima: float) -> bool:
        return self.separacion >= separacion_minima


@dataclass(frozen=True)
class BarraHistograma:
    """Cantidad de saltos |ΔP| que cayeron en [desde_kw, hasta_kw)."""

    desde_kw: float
    hasta_kw: float
    cantidad: int


@dataclass(frozen=True)
class CargaSimulada:
    """Equipo ON/OFF de un tablero simulado: cuánto consume, cuántas veces se prende y cuánto dura."""

    potencia_kw: float
    ciclos_por_dia: float
    duracion_min: float


@dataclass(frozen=True)
class EventoReal:
    """Encendido (+) o apagado (-) que realmente ocurrió: la "verdad" contra la que se evalúa."""

    instante: datetime
    delta_kw: float
    carga_kw: float


@dataclass(frozen=True)
class EventoDetectado:
    """Evento que encontró el algoritmo, con la carga a la que lo asignó (None si quedó sin grupo)."""

    instante: datetime
    delta_kw: float
    carga_kw: float | None


@dataclass(frozen=True)
class ResultadoCarga:
    """Qué tan bien se encontró una carga real."""

    potencia_real_kw: float
    eventos_reales: int
    detectados: int
    bien_asignados: int
    potencia_estimada_kw: float | None

    @property
    def sensibilidad(self) -> float:
        """De los eventos que ocurrieron, qué fracción se detectó y asignó a esta carga (recall)."""
        return self.bien_asignados / self.eventos_reales if self.eventos_reales else 0.0


@dataclass(frozen=True)
class Evaluacion:
    """Comparación entre lo que encontró el algoritmo y lo que realmente pasó."""

    por_carga: list[ResultadoCarga]
    eventos_detectados: int
    falsos_positivos: int
    cargas_inventadas: list[float]

    @property
    def precision(self) -> float:
        """De los eventos detectados, qué fracción corresponde a un evento real."""
        if not self.eventos_detectados:
            return 0.0
        return (self.eventos_detectados - self.falsos_positivos) / self.eventos_detectados
