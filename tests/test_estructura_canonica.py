"""tests/test_estructura_canonica.py — Cada bounded context respeta la estructura del spec.

Fuente: srs-spec-backend-fastapi.md §4.2 (datamaq-automation/spec). Por cada
contexto `{bc}` que aparezca en src/domain, src/application o src/adapters exige:

  src/domain/{bc}/       entities, value_objects, services, repositories, events, exceptions
  src/application/{bc}/  use_cases/, dtos/ (con *Request y *Response), mappers/
  src/adapters/{bc}/     controllers/, presenters/, gateways/ (view_models/ opcional)

y que no haya código Python fuera de src/ y tests/ (salvo el entrypoint wsgi.py).

Uso:
  - Con Pytest:  pytest tests/test_estructura_canonica.py -v
  - Como Script: python3 tests/test_estructura_canonica.py
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"

ARCHIVOS_DOMINIO = frozenset(
    {
        "__init__.py",
        "entities.py",
        "value_objects.py",
        "services.py",
        "repositories.py",
        "events.py",
        "exceptions.py",
    }
)
CARPETAS_APLICACION = frozenset({"use_cases", "dtos", "mappers"})
CARPETAS_ADAPTADORES = frozenset({"controllers", "presenters", "gateways"})
CARPETAS_ADAPTADORES_OPCIONALES = frozenset({"view_models"})
ENTRADAS_SRC = frozenset(
    {"domain", "application", "adapters", "infrastructure", "main.py", "__init__.py"}
)
PY_PERMITIDOS_EN_RAIZ = frozenset({"wsgi.py"})
DIRECTORIOS_NO_ANALIZADOS = frozenset({".git", ".venv", "venv", "node_modules", "src", "tests"})

# Deuda conocida: cada entrada dice por qué todavía no cumple y dónde se resuelve.
# Al migrar un contexto, se borra su línea; el test vuelve a exigirle la estructura.
CONTEXTOS_PENDIENTES: dict[str, str] = {
    "cargas": "núcleo NILM anterior al spec (modelos.py/puertos.py); migración aparte",
    "crecidas": "en desarrollo en la rama feat/issue-9-crecidas (issue #9, PR #25)",
}
CODIGO_FUERA_DE_SRC_PENDIENTE: dict[str, str] = {
    "educacion": "lo lleva a src/ el PR #26 (issue #5)",
    "ventas": "lo lleva a src/ el PR #23 (issue #2)",
}


def _hijos(carpeta: Path) -> set[str]:
    return {p.name for p in carpeta.iterdir() if p.name != "__pycache__"}


def _modulos(carpeta: Path) -> list[Path]:
    return sorted(p for p in carpeta.glob("*.py") if p.name != "__init__.py")


def _clases(archivos: list[Path]) -> set[str]:
    nombres: set[str] = set()
    for archivo in archivos:
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        nombres |= {n.name for n in arbol.body if isinstance(n, ast.ClassDef)}
    return nombres


def contextos() -> list[str]:
    """Bounded contexts presentes en cualquiera de las tres capas internas."""
    encontrados: set[str] = set()
    for capa in ("domain", "application", "adapters"):
        carpeta = SRC / capa
        if carpeta.is_dir():
            encontrados |= {
                p.name for p in carpeta.iterdir() if p.is_dir() and p.name != "__pycache__"
            }
    return sorted(encontrados - CONTEXTOS_PENDIENTES.keys())


def verificar_dominio(bc: str) -> list[str]:
    carpeta = SRC / "domain" / bc
    if not carpeta.is_dir():
        return [f"[ESTRUCTURA] Falta src/domain/{bc}/"]
    hijos = _hijos(carpeta)
    errores = [f"[ESTRUCTURA] Falta src/domain/{bc}/{a}" for a in sorted(ARCHIVOS_DOMINIO - hijos)]
    errores += [
        f"[ESTRUCTURA] src/domain/{bc}/{a} no es un archivo canónico del dominio "
        f"(permitidos: {', '.join(sorted(ARCHIVOS_DOMINIO - {'__init__.py'}))})"
        for a in sorted(hijos - ARCHIVOS_DOMINIO)
    ]
    return errores


def _verificar_carpetas(
    capa: str, bc: str, obligatorias: frozenset[str], opcionales: frozenset[str]
) -> list[str]:
    carpeta = SRC / capa / bc
    if not carpeta.is_dir():
        return [f"[ESTRUCTURA] Falta src/{capa}/{bc}/"]
    hijos = _hijos(carpeta)
    errores = [f"[ESTRUCTURA] Falta src/{capa}/{bc}/{c}/" for c in sorted(obligatorias - hijos)]
    errores += [
        f"[ESTRUCTURA] src/{capa}/{bc}/{h} sobra: solo se admiten "
        f"{', '.join(sorted(obligatorias | opcionales))} y __init__.py"
        for h in sorted(hijos - obligatorias - opcionales - {"__init__.py"})
    ]
    if "__init__.py" not in hijos:
        errores.append(f"[ESTRUCTURA] Falta src/{capa}/{bc}/__init__.py")
    for sub in sorted((obligatorias | opcionales) & hijos):
        ruta = carpeta / sub
        if not (ruta / "__init__.py").is_file():
            errores.append(f"[ESTRUCTURA] Falta src/{capa}/{bc}/{sub}/__init__.py")
        if sub in obligatorias and not _modulos(ruta):
            errores.append(f"[ESTRUCTURA] src/{capa}/{bc}/{sub}/ no tiene ningún módulo")
    return errores


def verificar_aplicacion(bc: str) -> list[str]:
    errores = _verificar_carpetas("application", bc, CARPETAS_APLICACION, frozenset())
    dtos = SRC / "application" / bc / "dtos"
    if dtos.is_dir():
        clases = _clases(_modulos(dtos))
        for sufijo in ("Request", "Response"):
            if not any(nombre.endswith(sufijo) for nombre in clases):
                errores.append(
                    f"[ESTRUCTURA] src/application/{bc}/dtos/ no define ninguna clase *{sufijo}"
                )
    return errores


def verificar_adaptadores(bc: str) -> list[str]:
    return _verificar_carpetas(
        "adapters", bc, CARPETAS_ADAPTADORES, CARPETAS_ADAPTADORES_OPCIONALES
    )


def verificar_raiz_de_src() -> list[str]:
    return [
        f"[ESTRUCTURA] src/{h} está fuera de las cuatro capas: movelo a domain/application/adapters/infrastructure"
        for h in sorted(_hijos(SRC) - ENTRADAS_SRC)
    ]


def verificar_codigo_fuera_de_src() -> list[str]:
    errores: list[str] = []
    for entrada in sorted(RAIZ.iterdir()):
        if (
            entrada.is_file()
            and entrada.suffix == ".py"
            and entrada.name not in PY_PERMITIDOS_EN_RAIZ
        ):
            errores.append(f"[ESTRUCTURA] {entrada.name} está en la raíz: el código va en src/")
        if (
            entrada.is_dir()
            and entrada.name not in DIRECTORIOS_NO_ANALIZADOS
            and entrada.name not in CODIGO_FUERA_DE_SRC_PENDIENTE
            and any(entrada.rglob("*.py"))
        ):
            errores.append(f"[ESTRUCTURA] {entrada.name}/ tiene código Python fuera de src/")
    return errores


def verificar_estructura() -> list[str]:
    errores = verificar_raiz_de_src() + verificar_codigo_fuera_de_src()
    for bc in contextos():
        errores += verificar_dominio(bc) + verificar_aplicacion(bc) + verificar_adaptadores(bc)
    return errores


def test_bounded_contexts_con_estructura_canonica() -> None:
    errores = verificar_estructura()
    assert not errores, "\n".join(errores)


def test_las_excepciones_siguen_existiendo() -> None:
    """Una excepción que ya no hace falta se borra: así el test vuelve a cubrir ese contexto."""
    sobrantes = [bc for bc in CONTEXTOS_PENDIENTES if not (SRC / "domain" / bc).is_dir()]
    sobrantes += [d for d in CODIGO_FUERA_DE_SRC_PENDIENTE if not (RAIZ / d).is_dir()]
    assert not sobrantes, f"Quitá de las listas de pendientes: {sobrantes}"


def main() -> None:
    errores = verificar_estructura()
    for error in errores:
        print(error)
    pendientes = {**CONTEXTOS_PENDIENTES, **CODIGO_FUERA_DE_SRC_PENDIENTE}
    for nombre, motivo in pendientes.items():
        print(f"[PENDIENTE] {nombre}: {motivo}")
    print(f"Contextos verificados: {', '.join(contextos())}")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
