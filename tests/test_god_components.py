"""tests/test_god_components.py — Detector Determinístico de Componentes Dios (God Objects).

Analiza el código fuente en src/ utilizando el Árbol de Sintaxis Abstracta (AST) de Python
y la librería estándar (cero dependencias externas obligatorias).

Detecta y reporta:
  1. Archivos Dios (God Files): Líneas de código efectivas excesivas.
  2. Clases Dios (God Classes): Clases con excesivos métodos o líneas de definición.
  3. Métodos/Funciones Dios (God Functions): Funciones con excesivas líneas o alta anidación.

Produce:
  - Salida legible por humanos con ranking (Top N) y alertas de umbrales.
  - Salida JSON estructurada (--json) para auditoría automática o consumo por LLMs.

Uso:
  - Con Pytest:  pytest tests/test_god_components.py -v
  - Como Script: python3 tests/test_god_components.py [--json] [--top 5]
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

# Umbrales determinísticos por defecto
DEFAULT_MAX_FILE_LINES = 400
DEFAULT_MAX_CLASS_METHODS = 15
DEFAULT_MAX_CLASS_LINES = 250
DEFAULT_MAX_FUNC_LINES = 60
DEFAULT_MAX_CYCLOMATIC = 10


@dataclass
class FunctionMetric:
    name: str
    file_path: str
    lineno: int
    lines_count: int
    complexity: int
    is_god: bool
    reason: str = ""


@dataclass
class ClassMetric:
    name: str
    file_path: str
    lineno: int
    lines_count: int
    methods_count: int
    is_god: bool
    reason: str = ""


@dataclass
class FileMetric:
    file_path: str
    total_lines: int
    code_lines: int
    is_god: bool
    reason: str = ""


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


def count_lines(content: str) -> tuple[int, int]:
    """Calcula (total_lineas, lineas_de_codigo_efectivas)."""
    lines = content.splitlines()
    total = len(lines)
    code = sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))
    return total, code


def calculate_complexity(node: ast.AST) -> int:
    """Calcula complejidad ciclomática aproximada (ramificaciones de control)."""
    branches = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.ExceptHandler,
        ast.With,
        ast.AsyncWith,
        ast.Assert,
        ast.IfExp,
    )
    score = 1
    for child in ast.walk(node):
        if isinstance(child, branches):
            score += 1
        elif isinstance(child, ast.BoolOp):
            score += len(child.values) - 1
    return score


def analyze_file(
    file_path: Path,
    root_path: Path,
    max_file_lines: int = DEFAULT_MAX_FILE_LINES,
    max_class_methods: int = DEFAULT_MAX_CLASS_METHODS,
    max_class_lines: int = DEFAULT_MAX_CLASS_LINES,
    max_func_lines: int = DEFAULT_MAX_FUNC_LINES,
    max_complexity: int = DEFAULT_MAX_CYCLOMATIC,
) -> tuple[FileMetric, list[ClassMetric], list[FunctionMetric]]:
    """Analiza un archivo Python y computa métricas a nivel archivo, clase y función."""
    content = file_path.read_text(encoding="utf-8")
    rel_path = file_path.relative_to(root_path).as_posix()
    total_lines, code_lines = count_lines(content)

    is_god_file = code_lines > max_file_lines
    file_reason = f"Supera límite de {max_file_lines} líneas de código ({code_lines})" if is_god_file else ""
    file_metric = FileMetric(
        file_path=rel_path,
        total_lines=total_lines,
        code_lines=code_lines,
        is_god=is_god_file,
        reason=file_reason,
    )

    classes_metrics: list[ClassMetric] = []
    functions_metrics: list[FunctionMetric] = []

    try:
        tree = ast.parse(content, filename=str(file_path))
    except Exception:
        return file_metric, classes_metrics, functions_metrics

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            end_lineno = getattr(node, "end_lineno", node.lineno)
            cls_lines = end_lineno - node.lineno + 1
            methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            method_count = len(methods)

            reasons = []
            if method_count > max_class_methods:
                reasons.append(f"{method_count} métodos (> {max_class_methods})")
            if cls_lines > max_class_lines:
                reasons.append(f"{cls_lines} líneas (> {max_class_lines})")

            is_god_class = len(reasons) > 0
            classes_metrics.append(
                ClassMetric(
                    name=node.name,
                    file_path=rel_path,
                    lineno=node.lineno,
                    lines_count=cls_lines,
                    methods_count=method_count,
                    is_god=is_god_class,
                    reason=", ".join(reasons),
                )
            )

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_lineno = getattr(node, "end_lineno", node.lineno)
            func_lines = end_lineno - node.lineno + 1
            complexity = calculate_complexity(node)

            reasons = []
            if func_lines > max_func_lines:
                reasons.append(f"{func_lines} líneas (> {max_func_lines})")
            if complexity > max_complexity:
                reasons.append(f"complejidad {complexity} (> {max_complexity})")

            is_god_func = len(reasons) > 0
            functions_metrics.append(
                FunctionMetric(
                    name=node.name,
                    file_path=rel_path,
                    lineno=node.lineno,
                    lines_count=func_lines,
                    complexity=complexity,
                    is_god=is_god_func,
                    reason=", ".join(reasons),
                )
            )

    return file_metric, classes_metrics, functions_metrics


def scan_directory(
    root_path: Path | None = None,
    max_file_lines: int = DEFAULT_MAX_FILE_LINES,
    max_class_methods: int = DEFAULT_MAX_CLASS_METHODS,
    max_class_lines: int = DEFAULT_MAX_CLASS_LINES,
    max_func_lines: int = DEFAULT_MAX_FUNC_LINES,
    max_complexity: int = DEFAULT_MAX_CYCLOMATIC,
) -> dict[str, Any]:
    """Escanea el directorio src/ y extrae todas las métricas agregadas."""
    root = root_path or find_project_root()
    src_dir = root / "src"

    all_files: list[FileMetric] = []
    all_classes: list[ClassMetric] = []
    all_functions: list[FunctionMetric] = []

    if src_dir.exists():
        for current_root, _, files in os.walk(src_dir):
            for file in files:
                if file.endswith(".py"):
                    full_path = Path(current_root) / file
                    f_met, c_mets, fn_mets = analyze_file(
                        full_path,
                        root,
                        max_file_lines,
                        max_class_methods,
                        max_class_lines,
                        max_func_lines,
                        max_complexity,
                    )
                    all_files.append(f_met)
                    all_classes.extend(c_mets)
                    all_functions.extend(fn_mets)

    # Ordenar de mayor a menor tamaño
    all_files.sort(key=lambda x: x.code_lines, reverse=True)
    all_classes.sort(key=lambda x: (x.methods_count, x.lines_count), reverse=True)
    all_functions.sort(key=lambda x: (x.lines_count, x.complexity), reverse=True)

    god_files = [f for f in all_files if f.is_god]
    god_classes = [c for c in all_classes if c.is_god]
    god_functions = [fn for fn in all_functions if fn.is_god]

    return {
        "summary": {
            "total_files_analyzed": len(all_files),
            "total_classes_analyzed": len(all_classes),
            "total_functions_analyzed": len(all_functions),
            "god_files_count": len(god_files),
            "god_classes_count": len(god_classes),
            "god_functions_count": len(god_functions),
            "requires_refactoring_review": bool(god_files or god_classes or god_functions),
        },
        "thresholds": {
            "max_file_lines": max_file_lines,
            "max_class_methods": max_class_methods,
            "max_class_lines": max_class_lines,
            "max_func_lines": max_func_lines,
            "max_complexity": max_complexity,
        },
        "god_components": {
            "files": [asdict(f) for f in god_files],
            "classes": [asdict(c) for c in god_classes],
            "functions": [asdict(fn) for fn in god_functions],
        },
        "top_rankings": {
            "top_files": [asdict(f) for f in all_files[:5]],
            "top_classes": [asdict(c) for c in all_classes[:5]],
            "top_functions": [asdict(fn) for fn in all_functions[:5]],
        },
    }


# ==============================================================================
# Baterías de Prueba para Pytest
# ==============================================================================


def test_no_critical_god_files():
    """Pytest: Verifica que ningún archivo supere el umbral crítico de God File."""
    results = scan_directory()
    god_files = results["god_components"]["files"]
    assert not god_files, f"Se detectaron {len(god_files)} archivos Dios: {god_files}"


def test_no_critical_god_classes():
    """Pytest: Verifica que ninguna clase supere el umbral crítico de God Class."""
    results = scan_directory()
    god_classes = results["god_components"]["classes"]
    assert not god_classes, f"Se detectaron {len(god_classes)} clases Dios: {god_classes}"


def test_no_critical_god_functions():
    """Pytest: Verifica que ninguna función supere el umbral crítico de God Function."""
    results = scan_directory()
    god_funcs = results["god_components"]["functions"]
    assert not god_funcs, f"Se detectaron {len(god_funcs)} funciones Dios: {god_funcs}"


# ==============================================================================
# CLI Entrypoint
# ==============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detector Determinístico de God Components (Files, Classes, Functions)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Genera salida en formato JSON estructurado para LLMs",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Cantidad de elementos en el ranking superior",
    )
    parser.add_argument("--max-file-lines", type=int, default=DEFAULT_MAX_FILE_LINES)
    parser.add_argument("--max-class-methods", type=int, default=DEFAULT_MAX_CLASS_METHODS)
    parser.add_argument("--max-class-lines", type=int, default=DEFAULT_MAX_CLASS_LINES)
    parser.add_argument("--max-func-lines", type=int, default=DEFAULT_MAX_FUNC_LINES)
    parser.add_argument("--max-complexity", type=int, default=DEFAULT_MAX_CYCLOMATIC)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Falla con código de salida 1 si hay God Components",
    )

    args = parser.parse_args()

    data = scan_directory(
        max_file_lines=args.max_file_lines,
        max_class_methods=args.max_class_methods,
        max_class_lines=args.max_class_lines,
        max_func_lines=args.max_func_lines,
        max_complexity=args.max_complexity,
    )

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        if args.strict and data["summary"]["requires_refactoring_review"]:
            sys.exit(1)
        sys.exit(0)

    # Modo Humano / Consola
    summary = data["summary"]
    print("=" * 70)
    print("🔍 REPORTE DETERMINÍSTICO DE COMPONENTES DIOS (God Objects)")
    print("=" * 70)
    print(f"📁 Archivos analizados: {summary['total_files_analyzed']}")
    print(f"🏛️  Clases analizadas:   {summary['total_classes_analyzed']}")
    print(f"⚙️  Funciones analizadas: {summary['total_functions_analyzed']}")
    print("-" * 70)

    god_files = data["god_components"]["files"]
    god_classes = data["god_components"]["classes"]
    god_functions = data["god_components"]["functions"]

    if god_files:
        print(f"\n❌ [ALERTA] Archivos Dios detectados ({len(god_files)}):")
        for f in god_files:
            print(f"   • {f['file_path']} ({f['code_lines']} líneas de código) -> {f['reason']}")
    else:
        print("\n✅ [OK] Ningún archivo supera el umbral de God File.")

    if god_classes:
        print(f"\n❌ [ALERTA] Clases Dios detectadas ({len(god_classes)}):")
        for c in god_classes:
            print(f"   • {c['file_path']}:{c['lineno']} class {c['name']} -> {c['reason']}")
    else:
        print("✅ [OK] Ninguna clase supera el umbral de God Class.")

    if god_functions:
        print(f"\n❌ [ALERTA] Funciones/Métodos Dios detectados ({len(god_functions)}):")
        for fn in god_functions:
            print(f"   • {fn['file_path']}:{fn['lineno']} def {fn['name']} -> {fn['reason']}")
    else:
        print("✅ [OK] Ninguna función supera el umbral de God Function.")

    # Mostrar Top Rankings
    top_limit = args.top
    print("\n" + "=" * 70)
    print(f"📊 TOP {top_limit} COMPONENTES MÁS GRANDES (Candidatos a revisión)")
    print("=" * 70)

    print("\n📂 Top Archivos por líneas de código:")
    for idx, f in enumerate(data["top_rankings"]["top_files"][:top_limit], start=1):
        status = "⚠️ ALERTA" if f["is_god"] else "✓ OK"
        print(f"   {idx}. [{status}] {f['file_path']} ({f['code_lines']} LOC / {f['total_lines']} total)")

    print("\n🏛️ Top Clases por métodos y líneas:")
    for idx, c in enumerate(data["top_rankings"]["top_classes"][:top_limit], start=1):
        status = "⚠️ ALERTA" if c["is_god"] else "✓ OK"
        print(
            f"   {idx}. [{status}] {c['file_path']}:{c['lineno']} class {c['name']} ({c['methods_count']} métodos, {c['lines_count']} LOC)"
        )

    print("\n⚙️ Top Funciones por líneas y complejidad:")
    for idx, fn in enumerate(data["top_rankings"]["top_functions"][:top_limit], start=1):
        status = "⚠️ ALERTA" if fn["is_god"] else "✓ OK"
        print(
            f"   {idx}. [{status}] {fn['file_path']}:{fn['lineno']} def {fn['name']} ({fn['lines_count']} LOC, complejidad {fn['complexity']})"
        )

    print("\n" + "=" * 70)
    if summary["requires_refactoring_review"]:
        print("💡 SUGERENCIA PARA EL LLM / INGENIERO:")
        print("   Se encontraron componentes que superan los umbrales determinísticos.")
        print("   Evalúe aplicar refactorizaciones como Extract Class, Extract Method o desacoplar módulos.")
        print("=" * 70)
        if args.strict:
            sys.exit(1)
    else:
        print("🎉 No se detectaron componentes Dios. El código cumple los estándares de tamaño.")
        print("=" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
