"""src/domain/medioambiente/value_objects.py — Vocabulario y resultados inmutables del caso de CO."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

COLUMNA_CO = "CO(GT)"
COLUMNA_ETIQUETA = "episodio"
UMBRAL_EPISODIO_MG_M3 = 2.5  # Umbral pedagógico (mg/m³), no normativo.

COLUMNAS_METEO = ("T", "RH", "AH")
COLUMNAS_CALENDARIO = ("hora", "dia_semana", "mes")
# Features conocidas ANTES de la hora a predecir: meteo en t-1/t-2 (por reloj) + calendario.
# Lista (no tuple) para poder indexar: df[COLUMNAS_FEATURES].
COLUMNAS_FEATURES: list[str] = [f"{c}_t{lag}" for c in COLUMNAS_METEO for lag in (1, 2)] + list(
    COLUMNAS_CALENDARIO
)
# Nunca pueden entrar como entrada: salen de la misma hora o generan la etiqueta.
COLUMNAS_PROHIBIDAS = (
    "CO(GT)",
    "PT08.S1(CO)",
    "NMHC(GT)",
    "C6H6(GT)",
    "PT08.S2(NMHC)",
    "NOx(GT)",
    "PT08.S3(NOx)",
    "NO2(GT)",
    "PT08.S4(NO2)",
    "PT08.S5(O3)",
)

# La Tarea A agrupa por las variables meteorológicas de la misma hora: aquí NO hay
# predicción (no hay fuga posible), solo descripción de condiciones.
COLUMNAS_AGRUPAMIENTO: list[str] = ["T", "RH", "AH"]
K_MIN = 2
K_MAX = 6
SEMILLA = 42
PROFUNDIDADES_ARBOL = [3, 4, 5, 6]
PROPORCION_TRAIN = 0.8
UMBRAL_CAMBIO = 0.5  # desviación estándar de la media de train (tamaño de efecto)


class Particion(str, Enum):
    """Forma de separar train/test: la Tarea B usa la aleatoria, la Tarea C la temporal."""

    ALEATORIA = "aleatorio"
    TEMPORAL = "temporal"


@dataclass(frozen=True)
class DiagnosticoK:
    """Inercia (codo) y silueta de K-means para un valor de k."""

    k: int
    inercia: float
    silueta: float


@dataclass(frozen=True)
class PerfilGrupo:
    """Medias meteorológicas de un grupo y su proporción de episodios (solo interpretación)."""

    grupo: int
    horas: int
    temperatura_media: float
    humedad_relativa_media: float
    humedad_absoluta_media: float
    proporcion_episodio: float


@dataclass(frozen=True)
class MatrizConfusion:
    """Matriz 2x2 sobre las clases 0 (sin episodio) y 1 (episodio)."""

    verdaderos_negativos: int
    falsos_positivos: int
    falsos_negativos: int
    verdaderos_positivos: int


@dataclass(frozen=True)
class MetricasModelo:
    """Métricas de la clase 'episodio' de un modelo sobre el test de una partición."""

    modelo: str
    particion: Particion
    accuracy: float
    precision: float
    recall: float
    f1: float
    matriz: MatrizConfusion


@dataclass(frozen=True)
class CambioDistribucion:
    """Desplazamiento de la media de una feature entre train y test (en desvíos de train)."""

    feature: str
    media_train: float
    media_test: float
    desvio_estandarizado: float
    cambio: bool
