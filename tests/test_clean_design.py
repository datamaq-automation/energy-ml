"""tests/test_clean_design.py — Detector Determinístico de Código Muerto y Sobreingeniería.

Analiza el código fuente en src/ utilizando el Árbol de Sintaxis Abstracta (AST) de Python
y la librería estándar (cero dependencias externas obligatorias).

Detecta antipatrones de sobreingeniería y código muerto comunes en código generado por LLMs:
  1. GHOST_INTERFACE: Interfaces (Protocol/ABC) con 1 sola implementación concreta (YAGNI).
  2. MIDDLE_MAN_METHOD: Métodos pasamanos que solo delegan en otro objeto sin lógica agregada.
  3. DEEP_INHERITANCE: Árboles de herencia con profundidad mayor a 2 (DIT > 2).
  4. ORPHAN_PRIVATE_SYMBOL: Métodos, funciones o clases privadas declaradas pero nunca llamadas.
  5. SPECULATIVE_MICRO_FILE: Archivos micro-fragmentados (< 10 líneas de código efectivo).

Uso:
  python3 tests/test_clean_design.py           # Reporte visual
  python3 tests/test_clean_design.py --strict  # Falla (exit code 1) si hay violaciones críticas
  python3 tests/test_clean_design.py --json    # Salida JSON estructurada para LLMs / agentes
  pytest tests/test_clean_design.py -v         # Suite de pruebas automatizada
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DEFAULT_MAX_DIT = 2
DEFAULT_MIN_FILE_LOC = 10


@dataclass
class DesignIssue:
    code: str
    category: str
    file_path: str
    lineno: int
    symbol: str
    message: str
    suggestion: str


def find_project_root(start_path: Path | None = None) -> Path:
    """Encuentra la raíz del proyecto buscando el directorio 'src' hacia arriba."""
    if start_path is not None:
        current = start_path.resolve()
        for parent in [current, *current.parents]:
            if (parent / "src").is_dir():
                return parent
        return current

    script_dir = Path(__file__).resolve().parent
    for candidate in [script_dir, *script_dir.parents]:
        if (candidate / "src").is_dir():
            return candidate

    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (parent / "src").is_dir():
            return parent
    return Path.cwd().resolve()


def count_effective_lines(content: str) -> int:
    """Calcula líneas de código efectivas (sin comentarios ni líneas vacías)."""
    lines = content.splitlines()
    return sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))


def is_interface_class(node: ast.ClassDef) -> bool:
    """Detecta si una clase es una interfaz formal (ABC o Protocol)."""
    for base in node.bases:
        base_name = ""
        if isinstance(base, ast.Name):
            base_name = base.id
        elif isinstance(base, ast.Attribute):
            base_name = base.attr
        if base_name in ("ABC", "Protocol"):
            return True
    return False


def get_base_class_names(node: ast.ClassDef) -> list[str]:
    """Retorna los nombres de las clases base de una definición de clase."""
    names: list[str] = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
        elif isinstance(base, ast.Attribute):
            names.append(base.attr)
    return names


def is_middle_man_method(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Detecta si un método se limita a delegar en self.<attr>.<method>(*args) sin lógica."""
    if node.name.startswith("__") and node.name.endswith("__"):
        return False
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name) and dec.id in (
            "property",
            "abstractmethod",
            "override",
        ):
            return False

    body = node.body
    statements = [
        stmt
        for stmt in body
        if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))
    ]

    if len(statements) != 1:
        return False

    single_stmt = statements[0]
    if not isinstance(single_stmt, ast.Return) or single_stmt.value is None:
        return False

    call = single_stmt.value
    if not isinstance(call, ast.Call):
        return False

    func = call.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Attribute):
        root_obj = func.value.value
        if isinstance(root_obj, ast.Name) and root_obj.id == "self":
            param_names = [arg.arg for arg in node.args.args if arg.arg != "self"]
            call_args: list[str] = []
            for a in call.args:
                if isinstance(a, ast.Name):
                    call_args.append(a.id)
                else:
                    return False
            if param_names == call_args:
                return True

    return False


def scan_clean_design(
    root_path: Path | None = None,
    max_dit: int = DEFAULT_MAX_DIT,
    min_file_loc: int = DEFAULT_MIN_FILE_LOC,
) -> dict[str, Any]:
    """Escanea el proyecto en busca de código muerto y sobreingeniería."""
    root = find_project_root(root_path)
    src_dir = root / "src"
    tests_dir = root / "tests"

    issues: list[DesignIssue] = []

    if not src_dir.is_dir():
        return {
            "root_path": str(root),
            "total_issues": 0,
            "issues": [],
            "summary": {
                "ghost_interfaces": 0,
                "middle_man": 0,
                "deep_inheritance": 0,
                "orphan_symbols": 0,
                "micro_files": 0,
            },
        }

    all_classes: dict[str, list[dict[str, Any]]] = {}
    interface_defs: dict[str, dict[str, Any]] = {}
    inheritance_graph: dict[str, list[str]] = {}

    # 0. Grafo de Alcance (Reachability Graph de Archivos)
    all_src_files: set[str] = set()
    for current_root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                full_path = Path(current_root) / file
                rel_path = str(full_path.relative_to(root)).replace("\\", "/")
                all_src_files.add(rel_path)

    entrypoints: set[str] = set()
    main_py = src_dir / "main.py"
    if main_py.exists():
        entrypoints.add(str(main_py.relative_to(root)).replace("\\", "/"))

    if tests_dir.is_dir():
        for current_root, _, files in os.walk(tests_dir):
            for file in files:
                if file.endswith(".py"):
                    full_path = Path(current_root) / file
                    entrypoints.add(str(full_path.relative_to(root)).replace("\\", "/"))

    visited: set[str] = set()
    queue: list[str] = list(entrypoints)

    def resolve_python_import(module_name: str) -> str | None:
        if not module_name:
            return None
        parts = module_name.split(".")
        if parts[0] == "src":
            candidate = root / Path(*parts)
            py_file = candidate.with_suffix(".py")
            if py_file.exists():
                return str(py_file.relative_to(root)).replace("\\", "/")
            pkg_init = candidate / "__init__.py"
            if pkg_init.exists():
                return str(pkg_init.relative_to(root)).replace("\\", "/")
        return None

    while queue:
        current_rel = queue.pop(0)
        if current_rel in visited:
            continue
        visited.add(current_rel)

        full_p = root / current_rel
        if not full_p.exists():
            continue

        try:
            c = full_p.read_text(encoding="utf-8")
            t = ast.parse(c, filename=str(full_p))
        except Exception:
            continue

        for node in ast.walk(t):
            mod_names = []
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod_names.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod_names.append(node.module)

            for m in mod_names:
                res = resolve_python_import(m)
                if res and res not in visited:
                    queue.append(res)

    for src_rel in all_src_files:
        if src_rel not in visited:
            issues.append(
                DesignIssue(
                    code="UNREACHABLE_FILE",
                    category="Código Muerto",
                    file_path=src_rel,
                    lineno=1,
                    symbol=src_rel,
                    message=f"El archivo '{src_rel}' no es alcanzable desde src/main.py ni desde ninguna suite de tests.",
                    suggestion="Elimine el archivo si ya no se utiliza o conéctelo al flujo principal de importaciones.",
                )
            )

    scan_dirs = [src_dir]
    if tests_dir.is_dir():
        scan_dirs.append(tests_dir)

    for base_dir in scan_dirs:
        for current_root, _, files in os.walk(base_dir):
            for file in files:
                if not file.endswith(".py"):
                    continue
                file_path = Path(current_root) / file
                rel_path = str(file_path.relative_to(root)).replace("\\", "/")

                try:
                    file_content = file_path.read_text(encoding="utf-8")
                    tree = ast.parse(file_content, filename=str(file_path))
                except (OSError, SyntaxError, UnicodeDecodeError):
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        bases = get_base_class_names(node)
                        info = {
                            "name": node.name,
                            "file_path": rel_path,
                            "lineno": node.lineno,
                            "bases": bases,
                            "is_interface": is_interface_class(node),
                            "is_test": rel_path.startswith("tests/"),
                        }
                        all_classes.setdefault(node.name, []).append(info)
                        inheritance_graph[node.name] = bases

                        if info["is_interface"] and not info["is_test"]:
                            interface_defs[node.name] = info

    # Chequeo 1: GHOST_INTERFACE (Single-Implementation Abstractions)
    for iface_name, iface_info in interface_defs.items():
        implementations: list[dict[str, Any]] = []
        for _cls_name, cls_list in all_classes.items():
            for cls_info in cls_list:
                if iface_name in cls_info["bases"]:
                    implementations.append(cls_info)

        src_impls = [imp for imp in implementations if not imp["is_test"]]
        test_impls = [imp for imp in implementations if imp["is_test"]]

        if len(src_impls) == 1 and len(test_impls) == 0:
            impl_target = f"{src_impls[0]['name']} ({src_impls[0]['file_path']})"
            issues.append(
                DesignIssue(
                    code="GHOST_INTERFACE",
                    category="Sobreingeniería",
                    file_path=iface_info["file_path"],
                    lineno=iface_info["lineno"],
                    symbol=iface_name,
                    message=f"La interfaz/protocolo '{iface_name}' solo posee 1 implementación concreta en el sistema: {impl_target}.",
                    suggestion="Aplique YAGNI: Unifique en una clase concreta directa; evite abstracciones prematuras si no hay múltiples proveedores.",
                )
            )

    # Chequeo 2: DEEP_INHERITANCE (DIT > max_dit)
    def calculate_dit(class_name: str, visited: set[str] | None = None) -> int:
        if visited is None:
            visited = set()
        if class_name in visited or class_name not in inheritance_graph:
            return 0
        visited.add(class_name)
        bases = inheritance_graph.get(class_name, [])
        filtered_bases = [b for b in bases if b not in ("object", "ABC", "Protocol", "BaseModel")]
        if not filtered_bases:
            return 0
        return 1 + max(calculate_dit(b, visited.copy()) for b in filtered_bases)

    for cls_name, cls_list in all_classes.items():
        for cls_info in cls_list:
            if cls_info["is_test"] or cls_info["is_interface"]:
                continue
            dit = calculate_dit(cls_name)
            if dit > max_dit:
                issues.append(
                    DesignIssue(
                        code="DEEP_INHERITANCE",
                        category="Sobreingeniería",
                        file_path=cls_info["file_path"],
                        lineno=cls_info["lineno"],
                        symbol=cls_name,
                        message=f"La clase '{cls_name}' tiene una profundidad de herencia DIT={dit} (umbral máximo permitido: {max_dit}).",
                        suggestion="Priorice composición sobre herencia para reducir el acoplamiento y la fragilidad de clases base.",
                    )
                )

    # Chequeos a nivel de archivo dentro de src/
    for current_root, _, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(".py"):
                continue
            file_path = Path(current_root) / file
            rel_path = str(file_path.relative_to(root)).replace("\\", "/")

            try:
                file_content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(file_content, filename=str(file_path))
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue

            # Chequeo 5: SPECULATIVE_MICRO_FILE (< min_file_loc)
            if file != "__init__.py":
                loc = count_effective_lines(file_content)
                top_defs = [
                    n
                    for n in tree.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                ]
                if loc < min_file_loc and len(top_defs) <= 1:
                    issues.append(
                        DesignIssue(
                            code="SPECULATIVE_MICRO_FILE",
                            category="Sobreingeniería",
                            file_path=rel_path,
                            lineno=1,
                            symbol=file,
                            message=f"El archivo '{rel_path}' es un micro-archivo especulativo con solo {loc} líneas de código efectivo.",
                            suggestion="Evite la sobre-fragmentación. Co-ubique esta definición junto a su consumidor principal.",
                        )
                    )

            loaded_names: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    loaded_names.add(node.id)
                elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                    loaded_names.add(node.attr)

            for node in tree.body:
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name.startswith("_")
                    and not (node.name.startswith("__") and node.name.endswith("__"))
                    and node.name not in loaded_names
                ):
                    issues.append(
                        DesignIssue(
                            code="ORPHAN_PRIVATE_SYMBOL",
                            category="Código Muerto",
                            file_path=rel_path,
                            lineno=node.lineno,
                            symbol=f"def {node.name}",
                            message=f"La función privada '{node.name}' está declarada pero nunca es invocada en el módulo.",
                            suggestion="Elimine código muerto huérfano o agregue pruebas que justifiquen su existencia.",
                        )
                    )

                elif isinstance(node, ast.ClassDef):
                    if (
                        node.name.startswith("_")
                        and not (node.name.startswith("__") and node.name.endswith("__"))
                        and node.name not in loaded_names
                    ):
                        issues.append(
                            DesignIssue(
                                code="ORPHAN_PRIVATE_SYMBOL",
                                category="Código Muerto",
                                file_path=rel_path,
                                lineno=node.lineno,
                                symbol=f"class {node.name}",
                                message=f"La clase privada '{node.name}' está declarada pero nunca es referenciada en el módulo.",
                                suggestion="Elimine la clase privada no utilizada.",
                            )
                        )

                    for class_node in node.body:
                        if isinstance(class_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if is_middle_man_method(class_node):
                                issues.append(
                                    DesignIssue(
                                        code="MIDDLE_MAN_METHOD",
                                        category="Sobreingeniería",
                                        file_path=rel_path,
                                        lineno=class_node.lineno,
                                        symbol=f"{node.name}.{class_node.name}",
                                        message=f"El método '{node.name}.{class_node.name}' es un pasamanos puro (Middle Man) que delega idénticos argumentos sin lógica.",
                                        suggestion="Invoque directamente el componente subyacente o elimine la capa pasamanos innecesaria.",
                                    )
                                )

                            if (
                                class_node.name.startswith("_")
                                and not (
                                    class_node.name.startswith("__")
                                    and class_node.name.endswith("__")
                                )
                                and class_node.name not in loaded_names
                            ):
                                issues.append(
                                    DesignIssue(
                                        code="ORPHAN_PRIVATE_SYMBOL",
                                        category="Código Muerto",
                                        file_path=rel_path,
                                        lineno=class_node.lineno,
                                        symbol=f"{node.name}.{class_node.name}",
                                        message=f"El método privado '{node.name}.{class_node.name}' no es llamado internamente.",
                                        suggestion="Elimine el método no utilizado.",
                                    )
                                )

    summary = {
        "unreachable_files": sum(1 for i in issues if i.code == "UNREACHABLE_FILE"),
        "ghost_interfaces": sum(1 for i in issues if i.code == "GHOST_INTERFACE"),
        "middle_man": sum(1 for i in issues if i.code == "MIDDLE_MAN_METHOD"),
        "deep_inheritance": sum(1 for i in issues if i.code == "DEEP_INHERITANCE"),
        "orphan_symbols": sum(1 for i in issues if i.code == "ORPHAN_PRIVATE_SYMBOL"),
        "micro_files": sum(1 for i in issues if i.code == "SPECULATIVE_MICRO_FILE"),
    }

    return {
        "root_path": str(root),
        "total_issues": len(issues),
        "issues": [asdict(i) for i in issues],
        "summary": summary,
    }


def test_no_critical_clean_design_violations():
    """Pytest: Verifica que no existan violaciones de código muerto ni sobreingeniería."""
    results = scan_clean_design()
    issues = results["issues"]
    assert not issues, (
        f"Se detectaron {len(issues)} violaciones de diseño limpio / código muerto: {issues}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auditor Determinístico de Código Muerto y Sobreingeniería (YAGNI & KISS)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Emite salida JSON estructurada para LLMs"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Retorna exit code 1 si se detecta cualquier problema",
    )
    parser.add_argument(
        "--max-dit",
        type=int,
        default=DEFAULT_MAX_DIT,
        help="Profundidad máxima de herencia (DIT)",
    )
    parser.add_argument(
        "--min-file-loc",
        type=int,
        default=DEFAULT_MIN_FILE_LOC,
        help="Mínimo de LOC para no ser micro-archivo",
    )

    args = parser.parse_args()

    results = scan_clean_design(max_dit=args.max_dit, min_file_loc=args.min_file_loc)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        if args.strict and results["total_issues"] > 0:
            sys.exit(1)
        sys.exit(0)

    print("=" * 70)
    print("🧹 AUDITOR DETERMINÍSTICO DE CÓDIGO MUERTO Y SOBREINGENIERÍA (YAGNI)")
    print("=" * 70)
    print(f"📁 Raíz del proyecto: {results['root_path']}")
    print(f"🔍 Violaciones detectadas: {results['total_issues']}")
    print("-" * 70)

    summary = results["summary"]
    print(f"   • Archivos Huérfanos (Unreachable):  {summary['unreachable_files']}")
    print(f"   • Interfaces Fantasma (Single-Impl): {summary['ghost_interfaces']}")
    print(f"   • Métodos Pasamanos (Middle Man):     {summary['middle_man']}")
    print(f"   • Herencia Profunda (DIT > {args.max_dit}):       {summary['deep_inheritance']}")
    print(f"   • Símbolos Privados Huérfanos:       {summary['orphan_symbols']}")
    print(f"   • Micro-archivos Especulativos:       {summary['micro_files']}")
    print("-" * 70)

    if results["total_issues"] == 0:
        print("\n🎉 ¡Excelente! No se detectó código muerto ni sobreingeniería.")
        print("=" * 70)
        sys.exit(0)

    print("\n⚠️  DETALLE DE VIOLACIONES DETECTADAS:")
    for issue in results["issues"]:
        print(f"\n[{issue['code']}] {issue['file_path']}:{issue['lineno']} -> {issue['symbol']}")
        print(f"   Motivo:     {issue['message']}")
        print(f"   Sugerencia: {issue['suggestion']}")

    print("\n" + "=" * 70)
    if args.strict:
        print("💥 MODO STRICT: Se encontraron violaciones que deben corregirse.")
        print("=" * 70)
        sys.exit(1)
    else:
        print("💡 Revise las sugerencias anteriores para mantener el diseño simple y desacoplado.")
        print("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    main()
