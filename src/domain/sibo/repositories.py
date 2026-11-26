"""src/domain/sibo/repositories.py — Puertos del dominio SIBO que implementa la infraestructura."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Protocol

from src.domain.sibo.entities import Alimento, PrediccionPico, RegistroComida


class AlimentoRepository(Protocol):
    """Acceso a la base nutricional de alimentos."""

    def listar(self, busqueda: str | None = None) -> list[Alimento]: ...

    def obtener(self, alimento_id: int) -> Alimento | None: ...

    def listar_por_ids(self, ids: Iterable[int]) -> list[Alimento]: ...


class RegistroRepository(Protocol):
    """Persistencia de las comidas registradas por el usuario."""

    def crear(self, registro: RegistroComida) -> RegistroComida: ...

    def obtener(self, registro_id: int) -> RegistroComida | None: ...

    def listar(
        self,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[RegistroComida]: ...

    def eliminar(self, registro_id: int) -> bool: ...

    def registrar_sintomas_2h(
        self,
        registro_id: int,
        sintomas: float,
        fecha: datetime,
    ) -> RegistroComida | None: ...


class PredictorGases(Protocol):
    """Estimador del pico de gases y su banda para una comida."""

    def predecir_pico(
        self,
        alimento: Alimento,
        porcion_g: float,
        hora: float,
        sintomas: float,
    ) -> PrediccionPico: ...
