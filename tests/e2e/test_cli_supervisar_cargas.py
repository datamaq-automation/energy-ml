"""tests/e2e/test_cli_supervisar_cargas.py — ./run.sh supervise sobre un tablero simulado."""

from pathlib import Path

import pytest

from src.infrastructure.cli.simular_tablero import main as simular
from src.infrastructure.cli.supervisar_cargas import main as supervisar
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


def test_supervise_muestra_reglas_matriz_y_exactitud(
    simulado: None, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr("sys.argv", ["supervise"])
    with caplog.at_level("INFO", logger="backend-api"):
        supervisar()
    assert "Reglas que aprendió" in caplog.text
    assert "Matriz de confusión" in caplog.text
    assert "Exactitud:" in caplog.text


def test_supervise_rechaza_medidores_sin_verdad(
    simulado: None, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr("sys.argv", ["supervise", "planta_2_a"])
    supervisar()
    assert "No hay verdad conocida para planta_2_a" in caplog.text
