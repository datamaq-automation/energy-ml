"""tests/test_logging.py — El logging se configura en un único lugar."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
UNICO = RAIZ / "src" / "infrastructure" / "settings" / "logger.py"


def test_solo_logger_py_importa_logging() -> None:
    infractores = [
        str(p.relative_to(RAIZ))
        for carpeta in ("src",)
        for p in (RAIZ / carpeta).rglob("*.py")
        if p != UNICO
        and any(
            linea.strip() == "import logging" or linea.strip().startswith(("import logging.", "from logging"))
            for linea in p.read_text(encoding="utf-8").splitlines()
        )
    ]
    assert infractores == [], f"Importá `logger` desde src/infrastructure/settings/logger.py: {infractores}"
