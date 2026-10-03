#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# run.sh — Orquestador de Entorno y Tareas del Backend (FastAPI / Clean Arch)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"
PYTHON_BIN="${VENV_DIR}/bin/python"
PIP_BIN="${VENV_DIR}/bin/pip"
UVICORN_BIN="${VENV_DIR}/bin/uvicorn"
PYTEST_BIN="${VENV_DIR}/bin/pytest"
RUFF_BIN="${VENV_DIR}/bin/ruff"

ensure_venv() {
    if [[ ! -d "$VENV_DIR" ]]; then
        echo "📦 Creando entorno virtual en ${VENV_DIR}..."
        python3 -m venv "$VENV_DIR"
        "$PIP_BIN" install --upgrade pip
        if [[ -f "requirements-dev.txt" ]]; then
            echo "📥 Instalando dependencias desde requirements-dev.txt..."
            "$PIP_BIN" install -r requirements-dev.txt
        elif [[ -f "requirements.txt" ]]; then
            echo "📥 Instalando dependencias desde requirements.txt..."
            "$PIP_BIN" install -r requirements.txt
        fi
    fi
}

COMMAND="${1:-help}"

case "$COMMAND" in
    dev)
        ensure_venv
        echo "🚀 Iniciando servidor FastAPI en modo desarrollo (reload)..."
        exec "$UVICORN_BIN" src.main:app --reload --host 0.0.0.0 --port 8000
        ;;
    start)
        ensure_venv
        echo "🚀 Iniciando servidor FastAPI en modo producción..."
        exec "$UVICORN_BIN" src.main:app --host 0.0.0.0 --port 8000
        ;;
    test)
        ensure_venv
        echo "🧪 Ejecutando suite de pruebas con pytest..."
        exec "$PYTEST_BIN" "${@:2}"
        ;;
    gauntlet)
        ensure_venv
        echo "🛡️  Ejecutando Guantelete de Restricciones Arquitectónicas..."
        exec "$PYTHON_BIN" tests/test_architecture.py
        ;;
    audit)
        ensure_venv
        echo "🧹 Ejecutando auditorías determinísticas (Clean Design & God Components)..."
        "$PYTHON_BIN" tests/test_clean_design.py
        "$PYTHON_BIN" tests/test_god_components.py
        ;;
    lint)
        ensure_venv
        echo "🔍 Verificando linter y formato con ruff..."
        "$RUFF_BIN" check .
        "$RUFF_BIN" format --check .
        ;;
    format)
        ensure_venv
        echo "✨ Aplicando formato automático con ruff..."
        "$RUFF_BIN" format .
        "$RUFF_BIN" check --fix .
        ;;
    install)
        ensure_venv
        echo "📥 Actualizando dependencias en ${VENV_DIR}..."
        if [[ -f "requirements-dev.txt" ]]; then
            "$PIP_BIN" install -r requirements-dev.txt
        elif [[ -f "requirements.txt" ]]; then
            "$PIP_BIN" install -r requirements.txt
        fi
        ;;
    help|--help|-h)
        echo ""
        echo "Uso: ./run.sh [COMANDO] [OPCIONES]"
        echo ""
        echo "Comandos disponibles:"
        echo "  dev       : Levanta el servidor FastAPI con reload automático en puerto 8000"
        echo "  start     : Levanta el servidor FastAPI en modo producción"
        echo "  test      : Ejecuta la suite de pruebas unitarias y de arquitectura con pytest"
        echo "  gauntlet  : Ejecuta las 11 reglas del Guantelete de Restricciones (test_architecture.py)"
        echo "  audit     : Ejecuta auditorías de código muerto y componentes Dios"
        echo "  lint      : Comprueba errores de estilo y formato con ruff"
        echo "  format    : Formatea y corrige automáticamente el código con ruff"
        echo "  install   : Sincroniza las dependencias en el entorno virtual .venv"
        echo "  help      : Muestra esta ayuda"
        echo ""
        ;;
    *)
        echo "❌ Comando desconocido: $COMMAND"
        echo "Ejecute ./run.sh help para ver los comandos disponibles."
        exit 1
        ;;
esac
