"""src/domain/cargas/repositories.py — Puertos (interfaces) que el dominio necesita del exterior."""

from datetime import datetime
from typing import Protocol

from src.domain.cargas.entities import (
    Carga,
    DiagnosticoContingencia,
    DiagnosticoFirma,
    EventoCarga,
    EventoReal,
    FirmaElectrica,
    Medicion,
    Salto,
    TelemetriaTransformador,
)


class MedicionRepository(Protocol):
    """Fuente de series de potencia por medidor."""

    def medidores(self) -> list[str]:
        """Retorna lista de medidores disponibles."""
        ...

    def listar(self, medidor: str, desde: datetime, hasta: datetime) -> list[Medicion]: ...


class Bitacora(Protocol):
    """Registro de lo que hace el proceso (solo info, warning y error)."""

    def info(self, msg: str, *args: object) -> None: ...

    def warning(self, msg: str, *args: object) -> None: ...

    def error(self, msg: str, *args: object) -> None: ...


class AgrupadorEventos(Protocol):
    """Agrupa eventos por magnitud; devuelve una etiqueta por evento (-1 = ruido)."""

    def agrupar(
        self, eventos: list[EventoCarga], radio_kw: float, min_eventos: int
    ) -> list[int]: ...


class CargaRepository(Protocol):
    """Destino de las cargas identificadas de cada medidor."""

    def guardar(self, medidor: str, cargas: list[Carga]) -> None: ...


class VerdadRepository(Protocol):
    """Eventos reales de un medidor simulado: lo que el algoritmo debería encontrar."""

    def guardar(self, medidor: str, eventos: list[EventoReal]) -> None: ...

    def listar(self, medidor: str) -> list[EventoReal]: ...


class ClasificadorSaltos(Protocol):
    """Aprende de saltos etiquetados qué carga produjo cada uno, y lo predice en saltos nuevos."""

    def entrenar(self, saltos: list[Salto], etiquetas: list[str]) -> None: ...

    def predecir(self, saltos: list[Salto]) -> list[str]: ...

    def explicar(self) -> str:
        """Lo que aprendió el modelo, en texto legible."""
        ...

    def obtener_arbol_dict(self) -> dict:
        """Estructura del árbol de decisión como diccionario (JSON-serializable)."""
        ...

    def obtener_reglas_dict(self) -> dict:
        """Reglas extraídas del árbol como lista de diccionarios."""
        ...


class ClasificadorBayes(Protocol):
    """Clasificador probabilístico de contingencias para transformadores eléctricos."""

    def predecir_contingencia(
        self, telemetria: TelemetriaTransformador
    ) -> DiagnosticoContingencia: ...


class ClasificadorKNN(Protocol):
    """Clasificador basado en instancias (k-NN) para firmas eléctricas."""

    def clasificar_firma(
        self,
        firma: FirmaElectrica,
        k: int = 5,
        metrica: str = "euclidean",
    ) -> DiagnosticoFirma: ...
