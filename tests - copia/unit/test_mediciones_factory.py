"""tests/unit/test_mediciones_factory.py — Tests de la factoría de repositorios."""

from pathlib import Path

from src.infrastructure.csv.medicion_repository import CsvMedicionRepository
from src.infrastructure.mediciones_factory import crear_repositorio_mediciones
from src.infrastructure.ssh.medicion_repository import SshMedicionRepository


def test_crear_repositorio_local(tmp_path: Path) -> None:
    """Retorna CsvMedicionRepository en modo local."""
    repo = crear_repositorio_mediciones(source="local", csv_dir=str(tmp_path), cache_dir="dummy")

    assert isinstance(repo, CsvMedicionRepository)


def test_crear_repositorio_ssh(tmp_path: Path) -> None:
    """Retorna SshMedicionRepository en modo SSH."""
    repo = crear_repositorio_mediciones(source="ssh", csv_dir="dummy", cache_dir=str(tmp_path))

    assert isinstance(repo, SshMedicionRepository)


def test_lru_cache_retorna_misma_instancia_local(tmp_path: Path) -> None:
    """LRU cache: dos llamadas iguales retornan la misma instancia."""
    repo1 = crear_repositorio_mediciones(source="local", csv_dir=str(tmp_path), cache_dir="dummy")
    repo2 = crear_repositorio_mediciones(source="local", csv_dir=str(tmp_path), cache_dir="dummy")

    assert repo1 is repo2  # Misma instancia en memoria


def test_lru_cache_retorna_misma_instancia_ssh(tmp_path: Path) -> None:
    """LRU cache: dos llamadas iguales con SSH retornan la misma instancia."""
    repo1 = crear_repositorio_mediciones(source="ssh", csv_dir="dummy", cache_dir=str(tmp_path))
    repo2 = crear_repositorio_mediciones(source="ssh", csv_dir="dummy", cache_dir=str(tmp_path))

    assert repo1 is repo2


def test_lru_cache_diferentes_parametros(tmp_path: Path) -> None:
    """Parámetros distintos → instancias distintas (pero ambas cacheadas)."""
    repo_local = crear_repositorio_mediciones(
        source="local", csv_dir=str(tmp_path), cache_dir="dummy"
    )
    repo_ssh = crear_repositorio_mediciones(source="ssh", csv_dir="dummy", cache_dir=str(tmp_path))

    assert repo_local is not repo_ssh
    assert isinstance(repo_local, CsvMedicionRepository)
    assert isinstance(repo_ssh, SshMedicionRepository)


def test_lru_cache_clear_resetea_cache(tmp_path: Path) -> None:
    """Limpiar cache permite crear instancia nueva."""
    repo1 = crear_repositorio_mediciones(source="local", csv_dir=str(tmp_path), cache_dir="dummy")

    crear_repositorio_mediciones.cache_clear()

    repo2 = crear_repositorio_mediciones(source="local", csv_dir=str(tmp_path), cache_dir="dummy")

    # Después de cache_clear, son instancias distintas
    assert repo1 is not repo2
    assert isinstance(repo1, CsvMedicionRepository)
    assert isinstance(repo2, CsvMedicionRepository)
