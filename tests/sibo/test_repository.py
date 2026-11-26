"""tests/sibo/test_repository.py — Pruebas de los adaptadores SQLite y la semilla nutricional."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from src.adapters.sibo.gateways.alimento_repository import SqliteAlimentoRepository
from src.adapters.sibo.gateways.registro_repository import SqliteRegistroRepository
from src.domain.sibo.entities import RegistroComida
from src.infrastructure.sibo.database import BaseDatos
from src.infrastructure.sibo.ml.entrenamiento import cargar_muestras
from src.infrastructure.sibo.seed import sembrar_si_vacio

RUTA_SEMILLA = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "infrastructure"
    / "sibo"
    / "data"
    / "alimentos.csv"
)


def _base_datos(tmp_path: Path) -> BaseDatos:
    base_datos = BaseDatos(tmp_path / "sibo-test.db")
    base_datos.inicializar()
    return base_datos


def test_semilla_carga_y_no_duplica(tmp_path: Path) -> None:
    base_datos = _base_datos(tmp_path)

    assert sembrar_si_vacio(base_datos, RUTA_SEMILLA) >= 40
    assert sembrar_si_vacio(base_datos, RUTA_SEMILLA) == 0

    with base_datos.conexion() as conexion:
        alimentos = SqliteAlimentoRepository(conexion)
        assert len(alimentos.listar()) >= 40


def test_busqueda_y_obtencion_de_alimentos(tmp_path: Path) -> None:
    base_datos = _base_datos(tmp_path)
    sembrar_si_vacio(base_datos, RUTA_SEMILLA)

    with base_datos.conexion() as conexion:
        repositorio = SqliteAlimentoRepository(conexion)
        resultados = repositorio.listar("avena")
        assert [a.nombre for a in resultados] == ["Avena sin gluten"]

        primero = repositorio.listar()[0]
        assert repositorio.obtener(primero.id) == primero
        assert repositorio.obtener(9999) is None
        assert repositorio.listar_por_ids([]) == []


def test_registros_se_crean_listan_y_eliminan(tmp_path: Path) -> None:
    base_datos = _base_datos(tmp_path)
    sembrar_si_vacio(base_datos, RUTA_SEMILLA)

    with base_datos.conexion() as conexion:
        repositorio = SqliteRegistroRepository(conexion)
        creado = repositorio.crear(
            RegistroComida(
                fecha_hora=datetime(2026, 11, 7, 12, 30),
                alimento_id=1,
                porcion_g=80,
                sintomas=4,
                notas="prueba",
            )
        )
        assert creado.id is not None

        registros = repositorio.listar()
        assert len(registros) == 1
        assert registros[0].notas == "prueba"

        filtrados = repositorio.listar(
            desde=datetime(2026, 11, 7, 0, 0),
            hasta=datetime(2026, 11, 8, 0, 0),
        )
        assert len(filtrados) == 1
        assert repositorio.listar(desde=datetime(2026, 11, 8, 0, 0)) == []

        assert repositorio.eliminar(creado.id or 0) is True
        assert repositorio.eliminar(creado.id or 0) is False
        assert repositorio.listar() == []


def test_registrar_sintomas_2h_y_cargar_solo_etiquetas_validas(tmp_path: Path) -> None:
    base_datos = _base_datos(tmp_path)
    sembrar_si_vacio(base_datos, RUTA_SEMILLA)

    with base_datos.conexion() as conexion:
        repositorio = SqliteRegistroRepository(conexion)
        valido = repositorio.crear(
            RegistroComida(
                fecha_hora=datetime(2026, 11, 7, 12, 30),
                alimento_id=1,
                porcion_g=120,
                sintomas=3,
            )
        )
        invalido = repositorio.crear(
            RegistroComida(
                fecha_hora=datetime(2026, 11, 7, 13, 0),
                alimento_id=1,
                porcion_g=120,
                sintomas=0,
            )
        )
        assert valido.id is not None and invalido.id is not None

        actualizado = repositorio.registrar_sintomas_2h(valido.id, 8, datetime(2026, 11, 7, 14, 30))
        assert actualizado is not None
        assert actualizado.sintomas_2h == 8
        assert repositorio.obtener(valido.id) == actualizado
        assert repositorio.registrar_sintomas_2h(9999, 5, datetime(2026, 11, 7, 15, 0)) is None

        conexion.execute(
            """
            UPDATE registros
            SET sintomas_2h = 9, fecha_sintomas_2h = ?
            WHERE id = ?
            """,
            ("2026-11-07T13:30:00", invalido.id),
        )

        muestras = cargar_muestras(conexion)
        assert len(muestras) == 1
        assert muestras[0].etiqueta == 80.0


def test_migracion_agrega_columnas_de_seguimiento(tmp_path: Path) -> None:
    ruta = tmp_path / "sibo-antiguo.db"
    conexion = sqlite3.connect(ruta)
    conexion.execute(
        """
        CREATE TABLE registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL,
            alimento_id INTEGER NOT NULL,
            porcion_g REAL NOT NULL,
            sintomas REAL NOT NULL DEFAULT 0,
            notas TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conexion.commit()
    conexion.close()

    base_datos = BaseDatos(ruta)
    base_datos.inicializar()

    with base_datos.conexion() as conexion:
        columnas = {fila["name"] for fila in conexion.execute("PRAGMA table_info(registros)")}
    assert "sintomas_2h" in columnas
    assert "fecha_sintomas_2h" in columnas
