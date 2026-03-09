#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

source .venv/bin/activate

python -m pip install --upgrade pip

if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi
if [ -f pyproject.toml ]; then pip install -e . || true; fi

mkdir -p .tmp .cache/pyc .cache/mypy .cache/pip .localappdata

export TEMP="$ROOT/.tmp"
export TMP="$ROOT/.tmp"
export TMPDIR="$ROOT/.tmp"
export LOCALAPPDATA="$ROOT/.localappdata"
export PYTHONPYCACHEPREFIX="$ROOT/.cache/pyc"
export MYPY_CACHE_DIR="$ROOT/.cache/mypy"
export PIP_CACHE_DIR="$ROOT/.cache/pip"
export PYTEST_ADDOPTS="--basetemp=$ROOT/.tmp/pytest"

pytest -q

python scripts/preflight.py workspace.success.json

rm -rf .artifacts .artifacts_copy

python scripts/run_agent.py workspace.success.json

python scripts/verify.py workspace.success.json