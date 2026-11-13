"""Adaptador SQLite del repositorio de registros de comidas."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from sibo.domain.entities import RegistroComida
from sibo.infrastructure.sqlite.database import BaseDatos


class SqliteRegistroRepository:
    def __init__(self, base_datos: BaseDatos) -> None:
        self._base_datos = base_datos

    def crear(self, registro: RegistroComida) -> RegistroComida:
        with self._base_datos.conexion() as conexion:
            cursor = conexion.execute(
                """
                INSERT INTO registros (fecha_hora, alimento_id, porcion_g, sintomas, notas)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    registro.fecha_hora.isoformat(timespec="seconds"),
                    registro.alimento_id,
                    registro.porcion_g,
                    registro.sintomas,
                    registro.notas,
                ),
            )
            nuevo_id = int(cursor.lastrowid or 0)
        return replace(registro, id=nuevo_id)

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
        with self._base_datos.conexion() as conexion:
            filas = conexion.execute(consulta, parametros).fetchall()
        return [_desde_fila(fila) for fila in filas]

    def eliminar(self, registro_id: int) -> bool:
        with self._base_datos.conexion() as conexion:
            cursor = conexion.execute("DELETE FROM registros WHERE id = ?", (registro_id,))
            return cursor.rowcount > 0


def _desde_fila(fila: object) -> RegistroComida:
    return RegistroComida(
        id=fila["id"],
        fecha_hora=datetime.fromisoformat(fila["fecha_hora"]),
        alimento_id=fila["alimento_id"],
        porcion_g=fila["porcion_g"],
        sintomas=fila["sintomas"],
        notas=fila["notas"],
    )
