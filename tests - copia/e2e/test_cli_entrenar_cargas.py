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
        for i, kw in enumerate(
            120 + (0, 1, 2, 1)[j % 4] + (90 if (j // 3) % 2 else 0) for j in range(72)
        )
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
    assert lineas == ["potencia_tipica_kw,encendidos,apagados,ciclos", "90.0,12,11,11"]


def test_train_no_procesa_medidores_desconocidos(
    carpetas: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    _, salida = carpetas
    monkeypatch.setattr("sys.argv", ["train", "nada"])
    entrenar()
    assert not salida.exists()


def test_train_acepta_parametros_nilm_por_argumento(
    carpetas: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _, salida = carpetas
    monkeypatch.setattr(
        "sys.argv",
        ["train", "planta", "--umbral", "50", "--min-eventos", "4", "--balance-minimo", "0.9"],
    )
    with caplog.at_level("INFO", logger="backend-api"):
        entrenar()
    assert "Umbral fijo por configuración: 50.0 kW" in caplog.text
    assert "Mínimo fijo por configuración: 4 eventos" in caplog.text
    assert (salida / "cargas_planta.csv").exists()
    assert get_settings().NILM_UMBRAL_KW is None  # el argumento no modifica la configuración global


@pytest.mark.parametrize(
    "argumentos",
    [
        ["--umbral", "0"],
        ["--min-eventos", "0"],
        ["--separacion-minima", "1.5"],
        ["--balance-minimo", "-1"],
    ],
)
def test_train_rechaza_parametros_fuera_de_rango(
    carpetas: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, argumentos: list[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["train", *argumentos])
    with pytest.raises(SystemExit):
        entrenar()
