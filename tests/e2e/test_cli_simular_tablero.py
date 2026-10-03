"""tests/e2e/test_cli_simular_tablero.py — ./run.sh simulate escribe mediciones y verdad."""

from pathlib import Path

import pytest

from src.infrastructure.cli.simular_tablero import main as simular
from src.infrastructure.csv.medicion_repository import CsvMedicionRepository
from src.infrastructure.csv.verdad_repository import CsvVerdadRepository
from src.infrastructure.settings.config import get_settings


def test_simulate_genera_mediciones_y_verdad(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEDICIONES_CSV_DIR", str(tmp_path / "input"))
    monkeypatch.setenv("VERDAD_DIR", str(tmp_path / "verdad"))
    monkeypatch.setattr("sys.argv", ["simulate", "--nombre", "prueba", "--dias", "2"])
    get_settings.cache_clear()
    try:
        simular()
    finally:
        get_settings.cache_clear()
    assert CsvMedicionRepository(tmp_path / "input").medidores() == ["prueba"]
    assert CsvVerdadRepository(tmp_path / "verdad").listar("prueba")
