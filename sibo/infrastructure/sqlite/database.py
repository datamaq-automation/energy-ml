"""Conexión SQLite y esquema del módulo SIBO."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS alimentos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    categoria TEXT NOT NULL,
    porcion_base_g REAL NOT NULL,
    kcal REAL NOT NULL,
    proteinas_g REAL NOT NULL,
    carbohidratos_g REAL NOT NULL,
    grasas_g REAL NOT NULL,
    fibra_g REAL NOT NULL,
    fodmap TEXT NOT NULL,
    score_inflamatorio REAL NOT NULL,
    score_desinflamatorio REAL NOT NULL,
    notas TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_hora TEXT NOT NULL,
    alimento_id INTEGER NOT NULL REFERENCES alimentos(id),
    porcion_g REAL NOT NULL,
    sintomas REAL NOT NULL DEFAULT 0,
    notas TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_registros_fecha ON registros(fecha_hora);
"""


class BaseDatos:
    """Acceso de bajo nivel a un archivo SQLite local."""

    def __init__(self, ruta: str | Path) -> None:
        self._ruta = Path(ruta)

    @property
    def ruta(self) -> Path:
        return self._ruta

    @contextmanager
    def conexion(self) -> Iterator[sqlite3.Connection]:
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        conexion = sqlite3.connect(str(self._ruta))
        conexion.row_factory = sqlite3.Row
        try:
            yield conexion
            conexion.commit()
        finally:
            conexion.close()

    def inicializar(self) -> None:
        with self.conexion() as conexion:
            conexion.executescript(ESQUEMA)
