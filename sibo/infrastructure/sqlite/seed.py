"""Carga inicial del dataset nutricional semilla."""

from __future__ import annotations

import csv
from pathlib import Path

from sibo.infrastructure.sqlite.database import BaseDatos

COLUMNAS = [
    "id",
    "nombre",
    "categoria",
    "porcion_base_g",
    "kcal",
    "proteinas_g",
    "carbohidratos_g",
    "grasas_g",
    "fibra_g",
    "fodmap",
    "score_inflamatorio",
    "score_desinflamatorio",
    "notas",
]


def sembrar_si_vacio(base_datos: BaseDatos, ruta_csv: str | Path) -> int:
    """Inserta los alimentos del CSV si la tabla está vacía. Devuelve cuántos insertó."""
    with base_datos.conexion() as conexion:
        total = conexion.execute("SELECT COUNT(*) AS total FROM alimentos").fetchone()["total"]
        if total:
            return 0

        filas = _leer_csv(Path(ruta_csv))
        conexion.executemany(
            """
            INSERT OR IGNORE INTO alimentos (
                id, nombre, categoria, porcion_base_g, kcal, proteinas_g,
                carbohidratos_g, grasas_g, fibra_g, fodmap,
                score_inflamatorio, score_desinflamatorio, notas
            ) VALUES (
                :id, :nombre, :categoria, :porcion_base_g, :kcal, :proteinas_g,
                :carbohidratos_g, :grasas_g, :fibra_g, :fodmap,
                :score_inflamatorio, :score_desinflamatorio, :notas
            )
            """,
            filas,
        )
        return len(filas)


def _leer_csv(ruta: Path) -> list[dict[str, object]]:
    with ruta.open(encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo)
        return [
            {
                "id": int(fila["id"]),
                "nombre": fila["nombre"],
                "categoria": fila["categoria"],
                "porcion_base_g": float(fila["porcion_base_g"]),
                "kcal": float(fila["kcal"]),
                "proteinas_g": float(fila["proteinas_g"]),
                "carbohidratos_g": float(fila["carbohidratos_g"]),
                "grasas_g": float(fila["grasas_g"]),
                "fibra_g": float(fila["fibra_g"]),
                "fodmap": fila["fodmap"],
                "score_inflamatorio": float(fila["score_inflamatorio"]),
                "score_desinflamatorio": float(fila["score_desinflamatorio"]),
                "notas": fila.get("notas", ""),
            }
            for fila in lector
        ]
