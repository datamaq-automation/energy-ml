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

resolver_modo() {
    # Traduce el modo a la fuente que entiende la app (settings.MEDICIONES_SOURCE):
    # "dev" -> "local" (CSV en data/input), "prod" -> "ssh" (VPS). Retorna 1 si $1 no es un modo.
    case "$1" in
        dev)  export MEDICIONES_SOURCE="local" ;;
        prod) export MEDICIONES_SOURCE="ssh" ;;
        *)    return 1 ;;
    esac
    return 0
}

validar_ssh_prod() {
    # Preflight: valida conectividad SSH a VPS si está en modo prod
    if [[ "${MEDICIONES_SOURCE:-local}" == "ssh" ]]; then
        echo "🔐 Modo PROD: validando conectividad SSH a VPS..."
        if ! ssh -o BatchMode=yes -o ConnectTimeout=5 vps true 2>/dev/null; then
            echo "❌ No se puede conectar a VPS 'vps' via SSH."
            echo "   Asegúrate de:"
            echo "   1. Estar conectado a Tailscale"
            echo "   2. Tener ~/.ssh/config con entrada: Host vps ..."
            echo "   3. Clave pública instalada en VPS"
            exit 1
        fi
        echo "✅ Conectividad SSH validada"
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
        if resolver_modo "${2:-dev}"; then
            :  # resolver_modo ya exportó MEDICIONES_SOURCE
        fi
        if [[ "${MEDICIONES_SOURCE:-local}" == "ssh" ]]; then
            echo "🚀 Iniciando servidor FastAPI en modo producción (datos desde VPS)..."
        else
            echo "🚀 Iniciando servidor FastAPI en modo desarrollo (datos locales)..."
        fi
        validar_ssh_prod  # Exit si SSH falla
        exec "$UVICORN_BIN" src.main:app --host 0.0.0.0 --port 8000
        ;;
    train)
        ensure_venv
        ARGS=("${@:2}")
        if resolver_modo "${ARGS[0]:-}"; then
            ARGS=("${ARGS[@]:1}")  # Remover el primer argumento si era dev/prod
        fi
        echo "🧠 Identificando cargas (resultados en data/output/)..."
        exec "$PYTHON_BIN" -m src.infrastructure.cli.entrenar_cargas "${ARGS[@]}"
        ;;
    simulate)
        ensure_venv
        echo "🧪 Generando un tablero simulado con cargas conocidas..."
        exec "$PYTHON_BIN" -m src.infrastructure.cli.simular_tablero "${@:2}"
        ;;
    evaluate)
        ensure_venv
        ARGS=("${@:2}")
        if resolver_modo "${ARGS[0]:-}"; then
            ARGS=("${ARGS[@]:1}")
        fi
        echo "📏 Comparando lo identificado con la verdad conocida..."
        exec "$PYTHON_BIN" -m src.infrastructure.cli.evaluar_cargas "${ARGS[@]}"
        ;;
    supervise)
        ensure_venv
        ARGS=("${@:2}")
        if resolver_modo "${ARGS[0]:-}"; then
            ARGS=("${ARGS[@]:1}")
        fi
        echo "🎓 Entrenando un clasificador con la verdad de un medidor simulado..."
        exec "$PYTHON_BIN" -m src.infrastructure.cli.supervisar_cargas "${ARGS[@]}"
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
        echo "  start     : Levanta el servidor FastAPI (por defecto dev)"
        echo "              Opcional: dev (datos locales) o prod (datos desde VPS via SSH)"
        echo "              Uso: ./run.sh start dev    # datos en data/input/"
        echo "                   ./run.sh start prod   # datos descargados del VPS"
        echo "  train     : Identifica las cargas de data/input/ y guarda resultados en data/output/"
        echo "              Opcional: medidores y --desde/--hasta (ej. ./run.sh train planta_2_a --desde 2026-09-15)"
        echo "  simulate  : Genera data/input/sintetico.csv y su verdad en data/verdad/ (cargas conocidas)"
        echo "  evaluate  : Compara lo identificado con la verdad de un medidor simulado (sensibilidad, precisión)"
        echo "  supervise : Aprende las cargas de un medidor simulado con un árbol de decisión (supervisado)"
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
