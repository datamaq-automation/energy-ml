"""Adaptador SQLite del repositorio de alimentos."""

from __future__ import annotations

from collections.abc import Iterable

from sibo.domain.entities import Alimento
from sibo.infrastructure.sqlite.database import BaseDatos


class SqliteAlimentoRepository:
    def __init__(self, base_datos: BaseDatos) -> None:
        self._base_datos = base_datos

    def listar(self, busqueda: str | None = None) -> list[Alimento]:
        consulta = "SELECT * FROM alimentos"
        parametros: tuple[object, ...] = ()
        if busqueda:
            consulta += " WHERE nombre LIKE ? OR categoria LIKE ?"
            patron = f"%{busqueda.strip()}%"
            parametros = (patron, patron)
        consulta += " ORDER BY nombre"
        with self._base_datos.conexion() as conexion:
            filas = conexion.execute(consulta, parametros).fetchall()
        return [_desde_fila(fila) for fila in filas]

    def obtener(self, alimento_id: int) -> Alimento | None:
        with self._base_datos.conexion() as conexion:
            fila = conexion.execute(
                "SELECT * FROM alimentos WHERE id = ?", (alimento_id,)
            ).fetchone()
        return _desde_fila(fila) if fila else None

    def listar_por_ids(self, ids: Iterable[int]) -> list[Alimento]:
        identificadores = sorted(set(ids))
        if not identificadores:
            return []
        marcadores = ",".join("?" for _ in identificadores)
        with self._base_datos.conexion() as conexion:
            filas = conexion.execute(
                f"SELECT * FROM alimentos WHERE id IN ({marcadores})",  # noqa: S608
                identificadores,
            ).fetchall()
        return [_desde_fila(fila) for fila in filas]


def _desde_fila(fila: object) -> Alimento:
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
