#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_DIR}"

if [[ ! -x ".venv/bin/uvicorn" ]]; then
  echo "❌ No existe .venv. Ejecutá ./run.sh install en la raíz del proyecto."
  exit 1
fi

echo "🫁 Iniciando SIBO ML en http://localhost:8001"
exec .venv/bin/uvicorn sibo.main:app --reload --host 0.0.0.0 --port 8001
