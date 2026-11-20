"""src/application/crecidas/construir_dataset.py ? Implementaci?n del m?dulo."""

from dataclasses import dataclass
from datetime import date, timedelta

from src.domain.crecidas.modelos import NivelRio

NOMBRES_VARIABLES = (
    "tigre_dia_0",
    "san_fernando_dia_0",
    "tigre_dia_1",
    "san_fernando_dia_1",
    "tigre_dia_2",
    "san_fernando_dia_2",
    "tigre_dia_3",
    "san_fernando_dia_3",
)


@dataclass(frozen=True)
class DatasetCrecidas:
    """Datos preparados para entrenar y evaluar un horizonte de pronóstico."""

    fechas: list[date]
    variables: list[list[float]]
    objetivos: list[float]
    horizonte_dias: int

    def __post_init__(self) -> None:
        if not (
            len(self.fechas) == len(self.variables) == len(self.objetivos)
        ):
            raise ValueError("Fechas, variables y objetivos deben tener igual longitud.")
        if not self.fechas:
            raise ValueError("El dataset no contiene ejemplos.")
        if self.horizonte_dias not in (1, 2, 3):
            raise ValueError("El horizonte debe ser de 1, 2 o 3 días.")


def construir_dataset(
    niveles_tigre: list[NivelRio],
    niveles_san_fernando: list[NivelRio],
    horizonte_dias: int,
) -> DatasetCrecidas:
    """Construye ejemplos diarios usando únicamente observaciones disponibles hasta cada fecha."""
    if horizonte_dias not in (1, 2, 3):
        raise ValueError("El horizonte debe ser de 1, 2 o 3 días.")

    tigre = {nivel.instante.date(): nivel.nivel_m for nivel in niveles_tigre}
    san_fernando = {
        nivel.instante.date(): nivel.nivel_m for nivel in niveles_san_fernando
    }

    fechas: list[date] = []
    variables: list[list[float]] = []
    objetivos: list[float] = []

    for dia in sorted(tigre.keys() & san_fernando.keys()):
        dias_entrada = [dia - timedelta(days=atras) for atras in range(4)]
        dia_objetivo = dia + timedelta(days=horizonte_dias)

        if not all(
            fecha in tigre and fecha in san_fernando
            for fecha in dias_entrada
        ):
            continue

        if dia_objetivo not in tigre:
            continue

        fila: list[float] = []
        for fecha in dias_entrada:
            fila.extend((tigre[fecha], san_fernando[fecha]))

        fechas.append(dia)
        variables.append(fila)
        objetivos.append(tigre[dia_objetivo])

    return DatasetCrecidas(
        fechas=fechas,
        variables=variables,
        objetivos=objetivos,
        horizonte_dias=horizonte_dias,
    )
