"""tests/e2e/test_cli_entrenar_cargas.py — ./run.sh train de punta a punta sobre carpetas temporales."""

from pathlib import Path

import pytest

from src.infrastructure.cli.entrenar_cargas import main as entrenar
from src.infrastructure.settings.config import get_settings


@pytest.fixture
def carpetas(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    entrada, salida = tmp_path / "input", tmp_path / "output"
    entrada.mkdir()
    filas = [
        f"2026-09-20T{i // 12:02d}:{5 * (i % 12):02d}:00,{kw}"
        for i, kw in enumerate([120, 121, 210, 211] * 6)
    ]
    (entrada / "planta.csv").write_text(
        "instante,potencia_kw\n" + "\n".join(filas) + "\n", encoding="utf-8"
    )
    monkeypatch.setenv("MEDICIONES_CSV_DIR", str(entrada))
    monkeypatch.setenv("RESULTADOS_DIR", str(salida))
    get_settings.cache_clear()
    yield entrada, salida
    get_settings.cache_clear()


def test_train_guarda_las_cargas(
    carpetas: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    _, salida = carpetas
    monkeypatch.setattr("sys.argv", ["train", "planta"])
    entrenar()
    lineas = (salida / "cargas_planta.csv").read_text(encoding="utf-8").splitlines()
    assert lineas == ["potencia_tipica_kw,encendidos,apagados,ciclos", "89.9,6,5,5"]


def test_train_no_procesa_medidores_desconocidos(
    carpetas: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    _, salida = carpetas
    monkeypatch.setattr("sys.argv", ["train", "nada"])
    entrenar()
    assert not salida.exists()
