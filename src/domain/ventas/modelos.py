"""src/domain/ventas/modelos.py — Reglas del pronóstico de ventas: pistas, corte temporal y errores."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

COLUMNAS_VENTAS: tuple[str, ...] = ("date", "store", "item", "sales")
OBJETIVO: str = "sales"

# Pistas del pronóstico: solo información que ya se conoce el día anterior.
PISTAS: tuple[str, ...] = ("ayer", "semana_pasada", "dia", "mes")
COLUMNAS_PROHIBIDAS: tuple[str, ...] = (OBJETIVO,)

# Split temporal: se aprende con 2013-2016 y se evalúa con 2017.
FECHA_CORTE: str = "2017-01-01"

VALORES_K: tuple[int, ...] = (2, 3, 4, 5, 6)
K_ELEGIDO: int = 3

METODOS: tuple[str, ...] = ("ayer", "lineal", "bosque")

Serie = tuple[int, int]  # (tienda, producto)


@dataclass(frozen=True)
class MetricaGrupos:
    """Inercia (codo) y silueta de K-means para una cantidad de grupos k."""

    k: int
    inercia: float
    silueta: float


@dataclass(frozen=True)
class PerfilGrupo:
    """Resumen de un grupo de series: cuántas son y cuánto venden por día."""

    grupo: int
    cantidad_series: int
    venta_media: float


@dataclass(frozen=True)
class Agrupamiento:
    """Resultado de la Tarea A: métricas por k, perfiles y grupo de cada serie."""

    metricas: tuple[MetricaGrupos, ...]
    perfiles: tuple[PerfilGrupo, ...]
    grupo_por_serie: dict[Serie, int]


@dataclass(frozen=True)
class Pronosticos:
    """Ventas reales del examen y el pronóstico de cada método, fila por fila."""

    series: tuple[Serie, ...]
    fechas: tuple[str, ...]
    reales: tuple[float, ...]
    por_metodo: dict[str, tuple[float, ...]]


@dataclass(frozen=True)
class ErrorMetodo:
    """Error de un método en el examen (Tarea B)."""

    metodo: str
    mae: float
    rmse: float


@dataclass(frozen=True)
class ErrorGrupo:
    """Error de un método dentro de un grupo de series (Tarea C)."""

    grupo: int
    metodo: str
    mae: float
    venta_media: float

    @property
    def error_relativo(self) -> float:
        """MAE dividido la venta media del grupo (0.10 = se equivoca un 10%)."""
        return self.mae / self.venta_media if self.venta_media else 0.0


def validar_sin_fuga(pistas: tuple[str, ...] | list[str]) -> None:
    """Falla si alguna pista usa la venta del mismo día que se quiere pronosticar."""
    filtradas = [p for p in pistas if p in COLUMNAS_PROHIBIDAS]
    if filtradas:
        raise ValueError(f"Fuga de datos: las pistas {filtradas} no se conocen al pronosticar.")


def calcular_mae(reales: tuple[float, ...], predichos: tuple[float, ...]) -> float:
    """Error absoluto medio: en promedio, cuántas unidades se equivoca."""
    _validar_largos(reales, predichos)
    return sum(abs(r - p) for r, p in zip(reales, predichos, strict=True)) / len(reales)


def calcular_rmse(reales: tuple[float, ...], predichos: tuple[float, ...]) -> float:
    """Raíz del error cuadrático medio: castiga más los errores grandes."""
    _validar_largos(reales, predichos)
    suma = sum((r - p) ** 2 for r, p in zip(reales, predichos, strict=True))
    return (suma / len(reales)) ** 0.5


def _validar_largos(reales: tuple[float, ...], predichos: tuple[float, ...]) -> None:
    """Exige dos listas no vacías y del mismo largo."""
    if not reales or len(reales) != len(predichos):
        raise ValueError("Se necesitan reales y predichos no vacíos y del mismo largo.")


def errores_por_metodo(pronosticos: Pronosticos) -> list[ErrorMetodo]:
    """Tarea B: MAE y RMSE de cada método sobre todo el examen."""
    return [
        ErrorMetodo(
            metodo=metodo,
            mae=calcular_mae(pronosticos.reales, predichos),
            rmse=calcular_rmse(pronosticos.reales, predichos),
        )
        for metodo, predichos in pronosticos.por_metodo.items()
    ]


def errores_por_grupo(
    pronosticos: Pronosticos, grupo_por_serie: dict[Serie, int]
) -> list[ErrorGrupo]:
    """Tarea C: MAE de cada método separado por el grupo (Tarea A) de cada serie."""
    filas_por_grupo: dict[int, list[int]] = defaultdict(list)
    for fila, serie in enumerate(pronosticos.series):
        filas_por_grupo[grupo_por_serie[serie]].append(fila)

    errores: list[ErrorGrupo] = []
    for grupo in sorted(filas_por_grupo):
        filas = filas_por_grupo[grupo]
        reales = tuple(pronosticos.reales[f] for f in filas)
        for metodo, predichos in pronosticos.por_metodo.items():
            errores.append(
                ErrorGrupo(
                    grupo=grupo,
                    metodo=metodo,
                    mae=calcular_mae(reales, tuple(predichos[f] for f in filas)),
                    venta_media=sum(reales) / len(reales),
                )
            )
    return errores
