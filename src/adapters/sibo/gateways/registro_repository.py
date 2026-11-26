"""src/adapters/sibo/gateways/registro_repository.py — Adaptador SQLite de registros."""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import datetime

from src.domain.sibo.entities import RegistroComida


class SqliteRegistroRepository:
    """Repositorio de comidas que recibe la conexión por parámetro."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def crear(self, registro: RegistroComida) -> RegistroComida:
        cursor = self._conexion.execute(
            """
            INSERT INTO registros (
                fecha_hora, alimento_id, porcion_g, sintomas, notas,
                sintomas_2h, fecha_sintomas_2h
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                registro.fecha_hora.isoformat(timespec="seconds"),
                registro.alimento_id,
                registro.porcion_g,
                registro.sintomas,
                registro.notas,
                registro.sintomas_2h,
                registro.fecha_sintomas_2h.isoformat(timespec="seconds")
                if registro.fecha_sintomas_2h
                else None,
            ),
        )
        return replace(registro, id=int(cursor.lastrowid or 0))

    def obtener(self, registro_id: int) -> RegistroComida | None:
        fila = self._conexion.execute(
            "SELECT * FROM registros WHERE id = ?", (registro_id,)
        ).fetchone()
        return _desde_fila(fila) if fila else None

    def listar(
        self,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[RegistroComida]:
        consulta = "SELECT * FROM registros"
        condiciones: list[str] = []
        parametros: list[object] = []
        if desde is not None:
            condiciones.append("fecha_hora >= ?")
            parametros.append(desde.isoformat(timespec="seconds"))
        if hasta is not None:
            condiciones.append("fecha_hora <= ?")
            parametros.append(hasta.isoformat(timespec="seconds"))
        if condiciones:
            consulta += " WHERE " + " AND ".join(condiciones)
        consulta += " ORDER BY fecha_hora"
        filas = self._conexion.execute(consulta, parametros).fetchall()
        return [_desde_fila(fila) for fila in filas]

    def eliminar(self, registro_id: int) -> bool:
        cursor = self._conexion.execute("DELETE FROM registros WHERE id = ?", (registro_id,))
        return cursor.rowcount > 0

    def registrar_sintomas_2h(
        self,
        registro_id: int,
        sintomas: float,
        fecha: datetime,
    ) -> RegistroComida | None:
        cursor = self._conexion.execute(
            """
            UPDATE registros
            SET sintomas_2h = ?, fecha_sintomas_2h = ?
            WHERE id = ?
            """,
            (sintomas, fecha.isoformat(timespec="seconds"), registro_id),
        )
        if cursor.rowcount == 0:
            return None
        fila = self._conexion.execute(
            "SELECT * FROM registros WHERE id = ?", (registro_id,)
        ).fetchone()
        return _desde_fila(fila) if fila else None


def _desde_fila(fila: sqlite3.Row) -> RegistroComida:
    return RegistroComida(
        id=fila["id"],
        fecha_hora=datetime.fromisoformat(fila["fecha_hora"]),
        alimento_id=fila["alimento_id"],
        porcion_g=fila["porcion_g"],
        sintomas=fila["sintomas"],
        notas=fila["notas"],
        sintomas_2h=fila["sintomas_2h"],
        fecha_sintomas_2h=(
            datetime.fromisoformat(fila["fecha_sintomas_2h"]) if fila["fecha_sintomas_2h"] else None
        ),
    )
