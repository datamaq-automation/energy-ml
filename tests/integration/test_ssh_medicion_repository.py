"""tests/integration/test_ssh_medicion_repository.py — Tests del repositorio SSH."""

import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from src.infrastructure.ssh.medicion_repository import SshMedicionRepository


@pytest.fixture
def repo(tmp_path: Path) -> SshMedicionRepository:
    """Repositorio SSH con cache en tmp_path."""
    return SshMedicionRepository(cache_dir=tmp_path)


@pytest.fixture
def salida_mock() -> str:
    """Salida simulada de MySQL con dos medidores."""
    return "Trafo arriba\t2026-10-03 12:00:00\t92000\nTrafo abajo\t2026-10-03 12:00:00\t88000\n"


def test_parsear_salida_convierte_w_a_kw(repo: SshMedicionRepository) -> None:
    """Convierte watts a kilowatts correctamente."""
    salida = "Trafo arriba\t2026-10-03 12:00:00\t92000\n"
    por_medidor = repo._parsear_salida(salida)

    assert "Trafo arriba" in por_medidor
    assert len(por_medidor["Trafo arriba"]) == 1
    instante, potencia_kw = por_medidor["Trafo arriba"][0]
    assert instante == "2026-10-03T12:00:00"
    assert potencia_kw == 92.0


def test_parsear_salida_filtra_lineas_malformadas(repo: SshMedicionRepository) -> None:
    """Ignora líneas con menos de 3 campos."""
    salida = (
        "Trafo arriba\t2026-10-03 12:00:00\t92000\n"
        "Incompleto\t2026-10-03\n"  # Falta potencia
        "Trafo abajo\t2026-10-03 12:00:00\t88000\n"
    )
    por_medidor = repo._parsear_salida(salida)

    assert len(por_medidor) == 2
    assert "Trafo arriba" in por_medidor
    assert "Trafo abajo" in por_medidor


def test_parsear_salida_ignora_medidores_no_mapeados(repo: SshMedicionRepository) -> None:
    """Solo exporta medidores conocidos."""
    salida = (
        "Trafo arriba\t2026-10-03 12:00:00\t92000\n"
        "Medidor Desconocido\t2026-10-03 12:00:00\t50000\n"
    )
    por_medidor = repo._parsear_salida(salida)

    assert len(por_medidor) == 1
    assert "Trafo arriba" in por_medidor
    assert "Medidor Desconocido" not in por_medidor


def test_sincronizar_descarga_una_sola_vez(
    repo: SshMedicionRepository, monkeypatch: pytest.MonkeyPatch, salida_mock: str
) -> None:
    """La descarga es idempotente (una sola por proceso)."""
    llamadas = []

    def ejecutar_ssh_mock() -> str:
        llamadas.append(1)
        return salida_mock

    monkeypatch.setattr(repo, "_ejecutar_ssh", ejecutar_ssh_mock)

    # Primera llamada
    repo.sincronizar()
    assert len(llamadas) == 1
    assert repo._sincronizado

    # Segunda llamada (debe ignorarla)
    repo.sincronizar()
    assert len(llamadas) == 1  # Sin cambios


def test_listar_sincroniza_si_es_necesario(
    repo: SshMedicionRepository, monkeypatch: pytest.MonkeyPatch, salida_mock: str
) -> None:
    """listar() sincroniza automáticamente si es la primera llamada."""
    monkeypatch.setattr(repo, "_ejecutar_ssh", lambda: salida_mock)

    # Primera llamada a listar: debe sincronizar
    mediciones = repo.listar("planta_2_a", datetime(2026, 10, 1), datetime(2026, 10, 5))

    assert repo._sincronizado
    assert len(mediciones) > 0


def test_listar_filtra_por_rango_temporal(
    repo: SshMedicionRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Filtra mediciones por rango [desde, hasta)."""
    salida = (
        "Trafo arriba\t2026-10-03 10:00:00\t92000\n"
        "Trafo arriba\t2026-10-03 11:00:00\t92000\n"
        "Trafo arriba\t2026-10-03 12:00:00\t92000\n"
        "Trafo arriba\t2026-10-03 13:00:00\t92000\n"
    )
    monkeypatch.setattr(repo, "_ejecutar_ssh", lambda: salida)

    mediciones = repo.listar(
        "planta_2_a", datetime(2026, 10, 3, 11, 0), datetime(2026, 10, 3, 13, 0)
    )

    # Debe incluir las de 11:00 y 12:00, pero NO la de 10:00 ni 13:00
    assert len(mediciones) == 2
    assert mediciones[0].instante == datetime(2026, 10, 3, 11, 0)
    assert mediciones[1].instante == datetime(2026, 10, 3, 12, 0)


def test_listar_medidor_desconocido_lanza_error(
    repo: SshMedicionRepository, monkeypatch: pytest.MonkeyPatch, salida_mock: str
) -> None:
    """Medidor inexistente lanza LookupError."""
    monkeypatch.setattr(repo, "_ejecutar_ssh", lambda: salida_mock)
    repo.sincronizar()

    with pytest.raises(LookupError, match="Medidor desconocido"):
        repo.listar("medidor_fantasma", datetime(2026, 10, 1), datetime(2026, 10, 5))


def test_ejecutar_ssh_timeout_lanza_runtime_error(
    repo: SshMedicionRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Timeout SSH lanza RuntimeError descriptivo."""

    def subprocess_run_timeout(*args, **kwargs):  # type: ignore
        raise subprocess.TimeoutExpired("ssh", 30)

    monkeypatch.setattr("subprocess.run", subprocess_run_timeout)

    with pytest.raises(RuntimeError, match="Timeout SSH"):
        repo._ejecutar_ssh()


def test_ejecutar_ssh_falla_lanza_runtime_error(
    repo: SshMedicionRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Error SSH lanza RuntimeError descriptivo."""

    def subprocess_run_error(*args, **kwargs):  # type: ignore
        raise subprocess.CalledProcessError(1, "ssh", stderr="Connection refused")

    monkeypatch.setattr("subprocess.run", subprocess_run_error)

    with pytest.raises(RuntimeError, match="Error al conectar a VPS"):
        repo._ejecutar_ssh()


def test_ultima_descarga_info_en_ssh(
    repo: SshMedicionRepository, monkeypatch: pytest.MonkeyPatch, salida_mock: str
) -> None:
    """Metadatos de descarga después de sincronizar."""
    monkeypatch.setattr(repo, "_ejecutar_ssh", lambda: salida_mock)

    repo.sincronizar()
    info = repo.ultima_descarga_info()

    assert info["instante"] is not None
    assert info["duracion_segundos"] >= 0
    assert isinstance(info["filas_por_medidor"], dict)
    assert "Trafo arriba" in info["filas_por_medidor"]
    assert info["filas_por_medidor"]["Trafo arriba"] == 1
