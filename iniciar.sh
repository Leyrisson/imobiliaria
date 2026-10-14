#!/usr/bin/env bash
# imobiliaria — inicia a aplicação localmente (contrato Empresa IA)
set -euo pipefail
cd "$(dirname "$0")"
export PORT="${PORT:-5000}"
exec python3 app.py
