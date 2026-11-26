"""src/adapters/sibo/gateways/alimento_repository.py — Adaptador SQLite de alimentos."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable

from src.domain.sibo.entities import Alimento


class SqliteAlimentoRepository:
    """Repositorio de alimentos que recibe la conexión por parámetro."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def listar(self, busqueda: str | None = None) -> list[Alimento]:
        consulta = "SELECT * FROM alimentos"
        parametros: tuple[object, ...] = ()
        if busqueda:
            consulta += " WHERE nombre LIKE ? OR categoria LIKE ?"
            patron = f"%{busqueda.strip()}%"
            parametros = (patron, patron)
        consulta += " ORDER BY nombre"
        filas = self._conexion.execute(consulta, parametros).fetchall()
        return [_desde_fila(fila) for fila in filas]

    def obtener(self, alimento_id: int) -> Alimento | None:
        fila = self._conexion.execute(
            "SELECT * FROM alimentos WHERE id = ?", (alimento_id,)
        ).fetchone()
        return _desde_fila(fila) if fila else None

    def listar_por_ids(self, ids: Iterable[int]) -> list[Alimento]:
        identificadores = sorted(set(ids))
        if not identificadores:
            return []
        marcadores = ",".join("?" for _ in identificadores)
        filas = self._conexion.execute(
            f"SELECT * FROM alimentos WHERE id IN ({marcadores})",
            identificadores,
        ).fetchall()
        return [_desde_fila(fila) for fila in filas]


def _desde_fila(fila: sqlite3.Row) -> Alimento:
    return Alimento(
        id=fila["id"],
        nombre=fila["nombre"],
        categoria=fila["categoria"],
        porcion_base_g=fila["porcion_base_g"],
        kcal=fila["kcal"],
        proteinas_g=fila["proteinas_g"],
        carbohidratos_g=fila["carbohidratos_g"],
        grasas_g=fila["grasas_g"],
        fibra_g=fila["fibra_g"],
        fodmap=fila["fodmap"],
        score_inflamatorio=fila["score_inflamatorio"],
        score_desinflamatorio=fila["score_desinflamatorio"],
        notas=fila["notas"],
    )
