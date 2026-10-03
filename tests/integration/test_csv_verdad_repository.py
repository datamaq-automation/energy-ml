"""tests/integration/test_csv_verdad_repository.py — Ida y vuelta de los eventos reales en CSV."""

from datetime import datetime
from pathlib import Path

import pytest

from src.domain.cargas.entities import EventoReal
from src.domain.cargas.repositories import VerdadRepository
from src.infrastructure.csv.verdad_repository import CsvVerdadRepository


def test_guardar_y_listar_devuelve_los_mismos_eventos(tmp_path: Path) -> None:
    repo: VerdadRepository = CsvVerdadRepository(tmp_path)
    eventos = [EventoReal(datetime(2026, 9, 1, 1, 25), 90.0, 90.0), EventoReal(datetime(2026, 9, 1, 1, 40), -90.0, 90.0)]
    repo.guardar("sim", eventos)
    assert repo.listar("sim") == eventos


def test_listar_un_medidor_sin_verdad_falla(tmp_path: Path) -> None:
    with pytest.raises(LookupError):
        CsvVerdadRepository(tmp_path).listar("planta_2_a")
