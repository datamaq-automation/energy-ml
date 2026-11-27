"""tests/integration/test_csv_medicion_repository.py — Lectura y filtrado por rango desde CSV."""

from datetime import datetime
from pathlib import Path

import pytest

from src.infrastructure.csv.medicion_repository import CsvMedicionRepository


def test_listar_filtra_por_rango(tmp_path: Path) -> None:
    (tmp_path / "planta.csv").write_text(
        "instante,potencia_kw\n2026-09-20T00:00:00,1.5\n2026-09-20T00:05:00,2.5\n2026-09-21T00:00:00,9.0\n",
        encoding="utf-8",
    )
    mediciones = CsvMedicionRepository(tmp_path).listar(
        "planta", datetime(2026, 9, 20), datetime(2026, 9, 21)
    )
    assert [m.potencia_kw for m in mediciones] == [1.5, 2.5]
    assert mediciones[0].instante == datetime(2026, 9, 20)


def test_listar_rechaza_medidores_que_no_son_csv_de_la_carpeta(tmp_path: Path) -> None:
    (tmp_path / "planta.csv").write_text("instante,potencia_kw\n", encoding="utf-8")
    repo = CsvMedicionRepository(tmp_path)
    assert repo.medidores() == ["planta"]
    with pytest.raises(LookupError):
        repo.listar("../.env", datetime(2026, 9, 20), datetime(2026, 9, 21))
