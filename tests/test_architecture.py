"""tests/test_architecture.py — El Guantelete de Restricciones Extremas (Clean Architecture & DDD).

Inspirado en la filosofía de Robert C. Martin ("Uncle Bob") sobre el desarrollo asistido por agentes IA:
"Rodear a los agentes de restricciones extremas para tener máxima confianza en el código producido."

Este archivo ejecuta un análisis estático exhaustivo mediante el Árbol de Sintaxis Abstracta (AST)
de Python y la librería estándar, sin dependencias externas obligatorias.

Batería de Pruebas ("The Constraint Gauntlet"):
  1. test_init_files_must_be_empty:
     - El 100% de los archivos __init__.py en src/ y tests/ deben tener exactamente 0 bytes.
  2. test_clean_architecture_compliance:
     - Domain: No importa application, adapters, infrastructure, fastapi ni ORMs/drivers de persistencia.
     - Application: No importa adapters, infrastructure, fastapi ni ORMs.
     - Adapters: No importa infrastructure ni fastapi/starlette.
     - Infrastructure (Routers): No importan ORMs directamente (controladores delgados).
  3. test_no_relative_imports:
     - Prohíbe terminantemente imports relativos ('from . import' / 'from .. import'). Solo 'from src...'.
  4. test_all_functions_have_type_annotations:
     - Exige que todas las funciones y métodos en domain y application especifiquen Type Hints en parámetros y retorno.
  5. test_no_hardcoded_secrets:
     - Detecta credenciales, passwords, tokens JWT o connection strings quemadas en código fuente.

Uso:
  - Con Pytest:  pytest tests/test_architecture.py -v
  - Como Script: python3 tests/test_architecture.py
"""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path


def find_project_root(start_path: Path | None = None) -> Path:
    """Encuentra la raíz del proyecto buscando el directorio 'src' hacia arriba."""
    if start_path is not None:
        current = start_path.resolve()
        for parent in [current, *current.parents]:
            if (parent / "src").is_dir():
                return parent
        return current

    # Priorizar ancestros del directorio donde reside este script
    script_dir = Path(__file__).resolve().parent
    for candidate in [script_dir, *script_dir.parents]:
        if (candidate / "src").is_dir():
            return candidate

    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (parent / "src").is_dir():
            return parent
    return Path.cwd().resolve()


def parse_ast_safely(file_path: Path) -> ast.AST | None:
    """Parsea un archivo Python a AST de forma segura."""
    try:
        content = file_path.read_text(encoding="utf-8")
        return ast.parse(content, filename=str(file_path))
    except Exception as e:
        print(f"[ERROR] No se pudo parsear {file_path}: {e}", file=sys.stderr)
        return None


def extract_imports(tree: ast.AST) -> list[tuple[str, int, bool]]:
    """Extrae todos los módulos importados en un árbol AST.

    Retorna lista de tuplas: (nombre_modulo, linea, es_relativo)
    """
    imports: list[tuple[str, int, bool]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    imports.append((alias.name, node.lineno, False))
        elif isinstance(node, ast.ImportFrom):
            is_relative = node.level is not None and node.level > 0
            module_name = node.module or ""
            imports.append((module_name, node.lineno, is_relative))
    return imports


# ==============================================================================
# 1. Verificación de Archivos __init__.py (0 bytes)
# ==============================================================================


def verify_init_files_empty(root_dir: Path | None = None) -> list[str]:
    """Verifica que todos los archivos __init__.py en src/ y tests/ tengan exactamente 0 bytes."""
    root = root_dir or find_project_root()
    errors: list[str] = []

    for target_dir in [root / "src", root / "tests"]:
        if not target_dir.exists() or not target_dir.is_dir():
            continue

        for current_root, _, files in os.walk(target_dir):
            for file in files:
                if file == "__init__.py":
                    full_path = Path(current_root) / file
                    size = full_path.stat().st_size
                    if size != 0:
                        rel_path = full_path.relative_to(root).as_posix()
                        errors.append(
                            f"[INIT NO VACÍO] '{rel_path}' tiene {size} bytes. Debe tener exactamente 0 bytes."
                        )

    return errors


# ==============================================================================
# 2. Verificación de Aislamiento de Dominio Puro (Core Agnóstico)
# ==============================================================================


def verify_domain_isolation(root_dir: Path | None = None) -> list[str]:
    """Verifica que el Core de Dominio (src/domain) no importe frameworks o I/O externos."""
    root = root_dir or find_project_root()
    src_dir = root / "src"
    domain_dir = src_dir / "domain"
    errors: list[str] = []

    if not domain_dir.exists():
        return []

    domain_forbidden = (
        "fastapi",
        "starlette",
        "sqlalchemy",
        "sqlmodel",
        "tortoise",
        "httpx",
        "requests",
        "aiohttp",
        "pymysql",
        "psycopg",
        "psycopg2",
        "asyncpg",
        "paho",
        "aiokafka",
        "kafka",
        "redis",
        "celery",
        "src.application",
        "src.adapters",
        "src.infrastructure",
        "src.main",
    )

    for current_root, _, files in os.walk(domain_dir):
        for file in files:
            if not file.endswith(".py") or file == "__init__.py":
                continue

            full_path = Path(current_root) / file
            rel_path = full_path.relative_to(root).as_posix()
            tree = parse_ast_safely(full_path)
            if not tree:
                continue

            imports = extract_imports(tree)
            for module_name, lineno, _ in imports:
                if any(module_name.startswith(pkg) for pkg in domain_forbidden):
                    errors.append(f"[DOMINIO VIOLADO] {rel_path}:{lineno} importa módulo prohibido '{module_name}'.")

    return errors


# ==============================================================================
# 3. Verificación de Flujo de Capas e Infraestructura (Clean Arch & Thin Controllers)
# ==============================================================================


def verify_application_and_adapters_layers(root_dir: Path | None = None) -> list[str]:
    """Verifica dependencias en application, adapters y que controllers no importen ORM directo."""
    root = root_dir or find_project_root()
    src_dir = root / "src"
    errors: list[str] = []

    if not src_dir.exists():
        return []

    application_forbidden = (
        "fastapi",
        "starlette",
        "sqlalchemy",
        "sqlmodel",
        "tortoise",
        "pymysql",
        "psycopg",
        "psycopg2",
        "asyncpg",
        "paho",
        "aiokafka",
        "kafka",
        "redis",
        "src.adapters",
        "src.infrastructure",
        "src.main",
    )

    adapters_forbidden = (
        "fastapi",
        "starlette",
        "src.infrastructure",
        "src.main",
    )

    for current_root, _, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(".py") or file == "__init__.py":
                continue

            full_path = Path(current_root) / file
            rel_path = full_path.relative_to(root).as_posix()
            tree = parse_ast_safely(full_path)
            if not tree:
                continue

            imports = extract_imports(tree)
            for module_name, lineno, _ in imports:
                if "src/application" in rel_path and any(module_name.startswith(pkg) for pkg in application_forbidden):
                    errors.append(f"[APLICACIÓN VIOLADA] {rel_path}:{lineno} importa módulo prohibido '{module_name}'.")

                elif "src/adapters" in rel_path and any(module_name.startswith(pkg) for pkg in adapters_forbidden):
                    errors.append(
                        f"[ADAPTADORES VIOLADO] {rel_path}:{lineno} importa módulo prohibido '{module_name}'."
                    )

                elif (
                    "src/infrastructure/fastapi/routers" in rel_path or "src/infrastructure/fastapi/routes" in rel_path
                ):
                    if any(module_name.startswith(pkg) for pkg in ("sqlalchemy", "sqlmodel")):
                        errors.append(
                            f"[THIN CONTROLLER VIOLADO] {rel_path}:{lineno} importa '{module_name}' directamente (debe delegar en use cases)."
                        )

    return errors


# ==============================================================================
# 3. Verificación de Imports Absolutos
# ==============================================================================


def verify_no_relative_imports(root_dir: Path | None = None) -> list[str]:
    """Verifica que ningún módulo en src/ contenga imports relativos."""
    root = root_dir or find_project_root()
    src_dir = root / "src"
    errors: list[str] = []

    if not src_dir.exists():
        return []

    for current_root, _, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(".py") or file == "__init__.py":
                continue

            full_path = Path(current_root) / file
            rel_path = full_path.relative_to(root).as_posix()
            tree = parse_ast_safely(full_path)
            if not tree:
                continue

            for module_name, lineno, is_relative in extract_imports(tree):
                if is_relative:
                    errors.append(
                        f"[IMPORT RELATIVO] {rel_path}:{lineno} usa import relativo '{module_name}'. Use 'from src...'."
                    )

    return errors


# ==============================================================================
# 4. Verificación de Tipado Estricto: Retorno de Funciones (Domain & Application)
# ==============================================================================


def verify_function_return_types(root_dir: Path | None = None) -> list[str]:
    """Verifica que todas las funciones en domain y application especifiquen tipo de retorno explícito."""
    root = root_dir or find_project_root()
    src_dir = root / "src"
    errors: list[str] = []

    if not src_dir.exists():
        return []

    target_layers = [src_dir / "domain", src_dir / "application"]

    for layer_dir in target_layers:
        if not layer_dir.exists():
            continue

        for current_root, _, files in os.walk(layer_dir):
            for file in files:
                if not file.endswith(".py") or file == "__init__.py":
                    continue

                full_path = Path(current_root) / file
                rel_path = full_path.relative_to(root).as_posix()
                tree = parse_ast_safely(full_path)
                if not tree:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_name = node.name
                        # Ignorar métodos mágicos especiales excepto __init__
                        if func_name.startswith("__") and func_name.endswith("__") and func_name != "__init__":
                            continue

                        if func_name != "__init__" and node.returns is None:
                            errors.append(
                                f"[FALTA TYPE HINT RETORNO] {rel_path}:{node.lineno} la función '{func_name}' no especifica tipo de retorno ('-> Type')."
                            )

    return errors


# ==============================================================================
# 5. Verificación de Tipado Estricto: Parámetros de Funciones (Domain & Application)
# ==============================================================================


def verify_function_arg_types(root_dir: Path | None = None) -> list[str]:
    """Verifica que todos los argumentos de funciones en domain y application tengan Type Annotation."""
    root = root_dir or find_project_root()
    src_dir = root / "src"
    errors: list[str] = []

    if not src_dir.exists():
        return []

    target_layers = [src_dir / "domain", src_dir / "application"]

    for layer_dir in target_layers:
        if not layer_dir.exists():
            continue

        for current_root, _, files in os.walk(layer_dir):
            for file in files:
                if not file.endswith(".py") or file == "__init__.py":
                    continue

                full_path = Path(current_root) / file
                rel_path = full_path.relative_to(root).as_posix()
                tree = parse_ast_safely(full_path)
                if not tree:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_name = node.name
                        if func_name.startswith("__") and func_name.endswith("__") and func_name != "__init__":
                            continue

                        for arg in node.args.args:
                            if arg.arg in ("self", "cls"):
                                continue
                            if arg.annotation is None:
                                errors.append(
                                    f"[FALTA TYPE HINT PARÁMETRO] {rel_path}:{node.lineno} el parámetro '{arg.arg}' en '{func_name}' no tiene type annotation."
                                )

    return errors


# ==============================================================================
# 8. Verificación de Observabilidad: Cero print() No Estructurado en Producción
# ==============================================================================


def verify_no_unstructured_prints(root_dir: Path | None = None) -> list[str]:
    """Detecta llamadas a print() directo en el código de producción (src/)."""
    root = root_dir or find_project_root()
    src_dir = root / "src"
    errors: list[str] = []

    if not src_dir.exists():
        return []

    for current_root, _, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            full_path = Path(current_root) / file
            rel_path = full_path.relative_to(root).as_posix()
            tree = parse_ast_safely(full_path)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                    errors.append(
                        f"[OBSERVABILIDAD] {rel_path}:{node.lineno} uso de 'print()' en producción. Utilice logging o structlog."
                    )

    return errors


# ==============================================================================
# 5. Verificación de Secretos y Parámetros Críticos Hardcodeados
# ==============================================================================


def verify_no_hardcoded_secrets(root_dir: Path | None = None) -> list[str]:
    """Detecta contraseñas, connection strings o tokens secretos quemados en el código."""
    root = root_dir or find_project_root()
    src_dir = root / "src"
    errors: list[str] = []

    if not src_dir.exists():
        return []

    suspicious_patterns = [
        (
            re.compile(
                r"""(?:password|secret_key|api_key|token)\s*=\s*['"][a-zA-Z0-9_\-]{8,}['"]""",
                re.IGNORECASE,
            ),
            "Posible credencial/token quemado en código",
        ),
        (
            re.compile(
                r"""(?:postgres|mysql|mariadb|mongodb):\/\/[^:]+:[^@]+@""",
                re.IGNORECASE,
            ),
            "Connection string con contraseña en código fuente",
        ),
        (
            re.compile(r"""['"]eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}""", re.IGNORECASE),
            "Token JWT quemado en código fuente",
        ),
    ]

    for current_root, _, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            full_path = Path(current_root) / file
            rel_path = full_path.relative_to(root).as_posix()

            # Excluir archivos de configuración donde se definan defaults de desarrollo seguros
            if "src/infrastructure/settings/config.py" in rel_path:
                continue

            try:
                lines = full_path.read_text(encoding="utf-8").splitlines()
                for lineno, line in enumerate(lines, start=1):
                    # Ignorar comentarios
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    for pattern, desc in suspicious_patterns:
                        if pattern.search(line):
                            errors.append(f"[SECRETO HARDCODEADO] {rel_path}:{lineno} {desc}. Centralice en Settings.")
            except Exception:
                pass

    return errors


# ==============================================================================
# 2. Verificación de Seguridad OWASP: Cero Concatenación / f-strings en SQL Crudo
# ==============================================================================


def verify_no_raw_sql_formatting(root_dir: Path | None = None) -> list[str]:
    """Detecta concatenación o formateo de strings en sentencias SQL crudas (text() o .execute())."""
    root = root_dir or find_project_root()
    src_dir = root / "src"
    errors: list[str] = []

    if not src_dir.exists():
        return []

    for current_root, _, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            full_path = Path(current_root) / file
            rel_path = full_path.relative_to(root).as_posix()
            tree = parse_ast_safely(full_path)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Detectar text(f"...") o text("..." % var) o text("...".format(...))
                    is_text_call = isinstance(node.func, ast.Name) and node.func.id == "text"
                    if is_text_call and node.args:
                        first_arg = node.args[0]
                        if isinstance(first_arg, ast.JoinedStr):
                            errors.append(
                                f"[SEGURIDAD SQL] {rel_path}:{node.lineno}: Uso de f-string dentro de text(...). Riesgo de inyección SQL (OWASP). Utilice bind parameters estructurados (:param)."
                            )
                        elif isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Mod):
                            errors.append(
                                f"[SEGURIDAD SQL] {rel_path}:{node.lineno}: Uso de operador '%' dentro de text(...). Riesgo de inyección SQL (OWASP). Utilice bind parameters estructurados (:param)."
                            )
                        elif (
                            isinstance(first_arg, ast.Call)
                            and isinstance(first_arg.func, ast.Attribute)
                            and first_arg.func.attr == "format"
                        ):
                            errors.append(
                                f"[SEGURIDAD SQL] {rel_path}:{node.lineno}: Uso de .format() dentro de text(...). Riesgo de inyección SQL (OWASP). Utilice bind parameters estructurados (:param)."
                            )

    return errors


# ==============================================================================
# 3. Verificación de Gobernanza de Entorno: Cero os.environ / os.getenv fuera de Settings
# ==============================================================================


def verify_no_os_environ_direct_access(root_dir: Path | None = None) -> list[str]:
    """Exige que las variables de entorno se consuman exclusivamente a través de Settings."""
    root = root_dir or find_project_root()
    src_dir = root / "src"
    errors: list[str] = []

    if not src_dir.exists():
        return []

    for current_root, _, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            full_path = Path(current_root) / file
            rel_path = full_path.relative_to(root).as_posix()

            # Permitir lectura directa de entorno únicamente en el módulo central de Settings
            if "src/infrastructure/settings/" in rel_path:
                continue

            tree = parse_ast_safely(full_path)
            if not tree:
                continue

            for node in ast.walk(tree):
                # Detectar os.getenv(...)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if (
                        isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "os"
                        and node.func.attr == "getenv"
                    ):
                        errors.append(
                            f"[GOBERNANZA ENTORNO] {rel_path}:{node.lineno}: Acceso directo a 'os.getenv()'. Centralice la configuración en Settings (src/infrastructure/settings/config.py)."
                        )
                # Detectar os.environ[...]
                elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute):
                    if (
                        isinstance(node.value.value, ast.Name)
                        and node.value.value.id == "os"
                        and node.value.attr == "environ"
                    ):
                        errors.append(
                            f"[GOBERNANZA ENTORNO] {rel_path}:{node.lineno}: Acceso directo a 'os.environ'. Centralice la configuración en Settings (src/infrastructure/settings/config.py)."
                        )

    return errors


# ==============================================================================
# 6. Verificación de Cabecera con Path Relativo (Trazabilidad Canónica)
# ==============================================================================


def verify_relative_path_headers(root_dir: Path | None = None) -> list[str]:
    """Verifica que todo archivo .py (excepto __init__.py) comience con su ruta relativa."""
    root = root_dir or find_project_root()
    errors: list[str] = []

    scan_dirs = [root / "src", root / "tests"]

    for base_dir in scan_dirs:
        if not base_dir.exists():
            continue

        for current_root, _, files in os.walk(base_dir):
            for file in files:
                if not file.endswith(".py") or file == "__init__.py":
                    continue

                full_path = Path(current_root) / file
                rel_path = full_path.relative_to(root).as_posix()

                try:
                    tree = parse_ast_safely(full_path)
                    docstring = ast.get_docstring(tree) if tree else None
                    first_line = ""
                    with open(full_path, encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            stripped = line.strip()
                            if stripped:
                                first_line = stripped
                                break

                    has_header = False
                    if (
                        docstring
                        and rel_path in docstring.strip().splitlines()[0]
                        or first_line.startswith("#")
                        and rel_path in first_line
                        or first_line.startswith(('"""', "'''"))
                        and rel_path in first_line
                    ):
                        has_header = True

                    if not has_header:
                        errors.append(
                            f'[CABECERA FALTANTE] {rel_path} debe comenzar con docstring o comentario con su ruta relativa exacta: """{rel_path}"""'
                        )
                except (OSError, UnicodeDecodeError) as e:
                    errors.append(f"[ERROR LECTURA] {rel_path}: {e}")

    return errors


# ==============================================================================
# Suite de Pruebas Pytest ("The Constraint Gauntlet")
# ==============================================================================


def test_no_hardcoded_secrets():
    """Restricción 1: Prohibido hardcodear contraseñas, tokens y connection strings en código."""
    errors = verify_no_hardcoded_secrets()
    assert not errors, f"\n❌ Se detectaron {len(errors)} secretos hardcodeados:\n\n" + "\n".join(
        f"  • {err}" for err in errors
    )


def test_no_raw_sql_formatting():
    """Restricción 2: Prohibida concatenación o f-strings en SQL crudo (text()). Riesgo de SQLi."""
    errors = verify_no_raw_sql_formatting()
    assert not errors, f"\n❌ Se detectaron {len(errors)} usos inseguros de SQL crudo:\n\n" + "\n".join(
        f"  • {err}" for err in errors
    )


def test_no_os_environ_direct_access():
    """Restricción 3: Prohibido acceder a os.environ u os.getenv fuera de Settings."""
    errors = verify_no_os_environ_direct_access()
    assert not errors, f"\n❌ Se detectaron {len(errors)} accesos no centralizados al entorno:\n\n" + "\n".join(
        f"  • {err}" for err in errors
    )


def test_domain_isolation():
    """Restricción 2: El Core de Dominio no debe depender de frameworks ni I/O."""
    errors = verify_domain_isolation()
    assert not errors, f"\n❌ Se detectaron {len(errors)} violaciones de aislamiento de dominio:\n\n" + "\n".join(
        f"  • {err}" for err in errors
    )


def test_application_and_adapters_layers():
    """Restricción 3: Las capas de Application, Adapters y Thin Controllers deben respetar Clean Architecture."""
    errors = verify_application_and_adapters_layers()
    assert not errors, (
        f"\n❌ Se detectaron {len(errors)} violaciones de capas en application/adapters:\n\n"
        + "\n".join(f"  • {err}" for err in errors)
    )


def test_function_return_types():
    """Restricción 4: 100% de funciones en domain y application deben especificar tipo de retorno explícito."""
    errors = verify_function_return_types()
    assert not errors, f"\n❌ Se detectaron {len(errors)} funciones sin tipo de retorno:\n\n" + "\n".join(
        f"  • {err}" for err in errors
    )


def test_function_arg_types():
    """Restricción 5: 100% de parámetros en funciones de domain y application deben tener Type Annotations."""
    errors = verify_function_arg_types()
    assert not errors, f"\n❌ Se detectaron {len(errors)} parámetros sin tipado:\n\n" + "\n".join(
        f"  • {err}" for err in errors
    )


def test_init_files_must_be_empty():
    """Restricción 6: El 100% de los archivos __init__.py deben tener exactamente 0 bytes."""
    errors = verify_init_files_empty()
    assert not errors, f"\n❌ Se detectaron {len(errors)} archivos __init__.py no vacíos:\n\n" + "\n".join(
        f"  • {err}" for err in errors
    )


def test_no_relative_imports():
    """Restricción 7: Todos los imports en src/ deben ser absolutos ('from src...')."""
    errors = verify_no_relative_imports()
    assert not errors, f"\n❌ Se detectaron {len(errors)} imports relativos prohibidos:\n\n" + "\n".join(
        f"  • {err}" for err in errors
    )


def test_no_unstructured_prints():
    """Restricción 8: Cero uso de print() no estructurado en producción (src/)."""
    errors = verify_no_unstructured_prints()
    assert not errors, f"\n❌ Se detectaron {len(errors)} prints no estructurados:\n\n" + "\n".join(
        f"  • {err}" for err in errors
    )


def test_relative_path_headers():
    """Restricción 9: Todo archivo .py (excepto __init__.py) debe comenzar con su ruta relativa."""
    errors = verify_relative_path_headers()
    assert not errors, f"\n❌ Se detectaron {len(errors)} archivos sin cabecera de path relativo:\n\n" + "\n".join(
        f"  • {err}" for err in errors
    )


# ==============================================================================
# CLI Runner Independiente
# ==============================================================================


def main() -> None:
    """Ejecuta el Guantelete Completo de Restricciones desde línea de comandos."""
    print("=" * 70)
    print("🛡️  EJECUTANDO EL GUANTELETE DE RESTRICCIONES (Uncle Bob Paradigm)")
    print("=" * 70)

    suites = [
        ("1. Seguridad & Secretos (Cero hardcoded)", verify_no_hardcoded_secrets()),
        (
            "2. Seguridad OWASP: Cero Inyección SQL en text()",
            verify_no_raw_sql_formatting(),
        ),
        (
            "3. Gobernanza de Entorno: Cero os.environ/getenv fuera de Settings",
            verify_no_os_environ_direct_access(),
        ),
        ("4. Aislamiento de Dominio Puro (Core Agnóstico)", verify_domain_isolation()),
        (
            "5. Flujo de Capas e Infraestructura (Clean Arch & Thin Controllers)",
            verify_application_and_adapters_layers(),
        ),
        (
            "6. Tipado Estricto: Retorno de Funciones (-> Type)",
            verify_function_return_types(),
        ),
        ("7. Tipado Estricto: Parámetros de Funciones", verify_function_arg_types()),
        ("8. Archivos __init__.py (0 bytes)", verify_init_files_empty()),
        ("9. Imports Absolutos (Prohibidos relativos)", verify_no_relative_imports()),
        (
            "10. Observabilidad: Cero print() No Estructurado",
            verify_no_unstructured_prints(),
        ),
        (
            "11. Cabecera de Path Relativo (Trazabilidad)",
            verify_relative_path_headers(),
        ),
    ]

    total_errors: list[str] = []

    for name, errors in suites:
        if errors:
            print(f"\n❌ [FALLÓ] {name}: {len(errors)} violaciones")
            for err in errors:
                print(f"   • {err}")
            total_errors.extend(errors)
        else:
            print(f"✅ [APROBADO] {name}")

    print("\n" + "=" * 70)
    if total_errors:
        print(f"💥 RESULTADO FINAL: {len(total_errors)} violaciones detectadas.")
        print("Los agentes o desarrolladores deben corregir el código para superar el guantelete.")
        print("=" * 70)
        sys.exit(1)
    else:
        print("🎉 RESULTADO FINAL: 100% de las restricciones arquitectónicas fueron superadas con éxito.")
        print("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    main()
