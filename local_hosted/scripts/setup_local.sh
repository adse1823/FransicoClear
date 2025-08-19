#!/usr/bin/env bash
# Bootstrap both backend and frontend venvs cleanly
set -euo pipefail

setup_venv() {
  local dir="$1"
  echo "[setup_local] Setting up venv in ${dir}..."
  cd "$dir"

  # remove old venv if it exists
  rm -rf .venv

  # create new venv
  python -m venv .venv

  # find venv python (POSIX or Windows)
  local PY
  if [[ -x ".venv/bin/python" ]]; then
    PY=".venv/bin/python"
  elif [[ -x ".venv/Scripts/python.exe" ]]; then
    PY=".venv/Scripts/python.exe"
  else
    echo "Error: could not locate venv python in ${dir}" >&2
    exit 1
  fi

  # upgrade pip + install dependencies
  "${PY}" -m pip install --upgrade pip
  "${PY}" -m pip install -r requirements.txt

  cd - >/dev/null
}

setup_venv "backend"
setup_venv "frontend"

echo "[setup_local] Done! You can now run: bash run_local.sh"
