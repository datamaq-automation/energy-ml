"""tests/integration/test_sql_medicion_repository.py — Repositorio SQL contra un esquema mínimo en SQLite."""

from datetime import datetime

import pytest
from sqlalchemy import Engine, create_engine, text

from src.domain.cargas.repositories import MedicionRepository
from src.infrastructure.sqlalchemy.medicion_repository import SqlMedicionRepository


@pytest.fixture
def engine() -> Engine:
    eng = create_engine("sqlite://")
    with eng.begin() as c:
        c.execute(text("CREATE TABLE devices (id TEXT, name TEXT)"))
        c.execute(
            text(
                "CREATE TABLE telemetry_instantaneous (device_id TEXT, recorded_at DATETIME,"
                " total_active_power REAL, es_dato_confiable INTEGER)"
            )
        )
        c.execute(text("INSERT INTO devices VALUES ('a', 'Trafo arriba'), ('b', 'Trafo abajo')"))
        c.execute(
            text(
                "INSERT INTO telemetry_instantaneous VALUES"
                " ('a', '2026-09-20 08:05:00', 212000, 1),"
                " ('a', '2026-09-20 08:00:00', 121000, 1),"
                " ('a', '2026-09-20 08:10:00', 999000, 0),"
                " ('a', '2026-09-20 08:15:00', NULL, 1),"
                " ('b', '2026-09-20 08:00:00', 50000, 1),"
                " ('a', '2026-09-21 08:00:00', 1000, 1)"
            )
        )
    return eng


def test_lista_en_kw_ordenado_y_filtrado(engine: Engine) -> None:
    repo: MedicionRepository = SqlMedicionRepository(engine)
    datos = repo.listar("Trafo arriba", datetime(2026, 9, 20), datetime(2026, 9, 21))
    assert [m.potencia_kw for m in datos] == [121.0, 212.0]
    assert datos[0].instante < datos[1].instante
