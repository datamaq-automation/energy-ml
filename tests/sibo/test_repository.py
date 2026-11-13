"""Pruebas de los adaptadores SQLite y la semilla nutricional."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sibo.domain.entities import RegistroComida
from sibo.infrastructure.sqlite.alimento_repository import SqliteAlimentoRepository
from sibo.infrastructure.sqlite.database import BaseDatos
from sibo.infrastructure.sqlite.registro_repository import SqliteRegistroRepository
from sibo.infrastructure.sqlite.seed import sembrar_si_vacio

RUTA_SEMILLA = Path(__file__).resolve().parents[2] / "sibo" / "data" / "alimentos.csv"


def _base_datos(tmp_path: Path) -> BaseDatos:
    base_datos = BaseDatos(tmp_path / "sibo-test.db")
    base_datos.inicializar()
    return base_datos


def test_semilla_carga_y_no_duplica(tmp_path: Path) -> None:
    base_datos = _base_datos(tmp_path)

    assert sembrar_si_vacio(base_datos, RUTA_SEMILLA) >= 40
    assert sembrar_si_vacio(base_datos, RUTA_SEMILLA) == 0

    alimentos = SqliteAlimentoRepository(base_datos)
    assert len(alimentos.listar()) >= 40


def test_busqueda_y_obtencion_de_alimentos(tmp_path: Path) -> None:
    base_datos = _base_datos(tmp_path)
    sembrar_si_vacio(base_datos, RUTA_SEMILLA)
    repositorio = SqliteAlimentoRepository(base_datos)

    resultados = repositorio.listar("avena")
    assert [a.nombre for a in resultados] == ["Avena sin gluten"]

    primero = repositorio.listar()[0]
    assert repositorio.obtener(primero.id) == primero
    assert repositorio.obtener(9999) is None
    assert repositorio.listar_por_ids([]) == []


def test_registros_se_crean_listan_y_eliminan(tmp_path: Path) -> None:
    base_datos = _base_datos(tmp_path)
    sembrar_si_vacio(base_datos, RUTA_SEMILLA)
    repositorio = SqliteRegistroRepository(base_datos)

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
