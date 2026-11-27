"""src/adapters/educacion/gateways/estudiantes_csv.py — Dataset local UCI 320 (student-mat.csv)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.domain.educacion.modelos import CLUSTER_FEATURES

#: Dataset local UCI 320 (separador ';'), relativo a la raíz del repositorio.
DATA_PATH = Path(__file__).resolve().parents[4] / "datos" / "educacion" / "student-mat.csv"


def load_students(path: Path = DATA_PATH) -> pd.DataFrame:
    """Carga el dataset de estudiantes (separador ';') y valida columnas y tipos."""
    df = pd.read_csv(path, sep=";")
    required = (*CLUSTER_FEATURES, "G3")
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el dataset: {missing}")
    if not pd.api.types.is_numeric_dtype(df["G3"]):
        raise ValueError("G3 debe ser numérica para construir la etiqueta de desaprobado.")
    return df


class EstudiantesCsv:
    """Implementa FuenteEstudiantes leyendo y validando el CSV local."""

    def __init__(self, path: Path = DATA_PATH) -> None:
        self._path = path

    def leer(self) -> pd.DataFrame:
        """Devuelve el dataset completo validado (395 estudiantes)."""
        return load_students(self._path)
