"""tests/e2e/test_cli_evaluar_cargas.py — ./run.sh evaluate sobre un tablero simulado."""

from pathlib import Path

import pytest

from src.infrastructure.cli.evaluar_cargas import main as evaluar
from src.infrastructure.cli.simular_tablero import main as simular
from src.infrastructure.settings.config import get_settings


@pytest.fixture
def simulado(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEDICIONES_CSV_DIR", str(tmp_path / "input"))
    monkeypatch.setenv("VERDAD_DIR", str(tmp_path / "verdad"))
    get_settings.cache_clear()
    monkeypatch.setattr("sys.argv", ["simulate", "--dias", "3"])
    simular()
    yield
    get_settings.cache_clear()


def test_evaluate_informa_la_sensibilidad_de_cada_carga_real(
    simulado: None, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr("sys.argv", ["evaluate"])
    with caplog.at_level("INFO", logger="backend-api"):
        evaluar()
    assert "Carga real de 90" in caplog.text
    assert "Precisión:" in caplog.text


def test_evaluate_rechaza_medidores_sin_verdad(
    simulado: None, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr("sys.argv", ["evaluate", "planta_2_a"])
    evaluar()
    assert "No hay verdad conocida para planta_2_a" in caplog.text
