"""tests/integration/test_csv_carga_repository.py — Escritura de cargas en CSV."""

from pathlib import Path

from src.domain.cargas.entities import Carga
from src.domain.cargas.repositories import CargaRepository
from src.infrastructure.csv.carga_repository import CsvCargaRepository


def test_guardar_escribe_un_csv_por_medidor(tmp_path: Path) -> None:
    repo: CargaRepository = CsvCargaRepository(tmp_path / "output")
    repo.guardar("planta", [Carga(potencia_tipica_kw=92.1, encendidos=411, apagados=378)])
    lineas = (tmp_path / "output" / "cargas_planta.csv").read_text(encoding="utf-8").splitlines()
    assert lineas == ["potencia_tipica_kw,encendidos,apagados,ciclos", "92.1,411,378,378"]
