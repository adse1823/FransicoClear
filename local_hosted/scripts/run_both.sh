#!/usr/bin/env bash
set -euo pipefail

# Always operate relative to this file's folder (scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"

# --- function to setup venv and install requirements ---
setup_venv() {
  local dir="$1"
  local reqfile="$2"

  echo "[setup] Checking environment for $dir..."

  # create venv if missing
  if [[ ! -d "${dir}/.venv" ]]; then
    echo "[setup] Creating virtual environment in ${dir}/.venv"
    python3 -m venv "${dir}/.venv"
  fi

  # activate venv (cross-platform: bin vs Scripts)
  if [[ -f "${dir}/.venv/bin/activate" ]]; then
    source "${dir}/.venv/bin/activate"
    echo "${dir} venv activated"
  elif [[ -f "${dir}/.venv/Scripts/activate" ]]; then
    source "${dir}/.venv/Scripts/activate"
    echo "${dir} venv activated"
  else
    echo "[setup] Error: cannot find activate script in ${dir}/.venv"
    exit 1
  fi

  # install/upgrade requirements if file exists
  if [[ -f "$reqfile" ]]; then
    echo "[setup] Installing/upgrading requirements from $reqfile..."
    pip install --upgrade pip setuptools wheel -q
    pip install -r "$reqfile" -q
  fi
}

# --- sanity checks ---
if [[ ! -d "${BACKEND_DIR}" ]]; then
  echo "Error: backend directory not found at: ${BACKEND_DIR}" >&2
  exit 1
fi
if [[ ! -f "${BACKEND_DIR}/run_backend.sh" ]]; then
  echo "Error: run_backend.sh not found at: ${BACKEND_DIR}/run_backend.sh" >&2
  exit 1
fi
if [[ ! -d "${FRONTEND_DIR}" ]]; then
  echo "Error: frontend directory not found at: ${FRONTEND_DIR}" >&2
  exit 1
fi
if [[ ! -f "${FRONTEND_DIR}/run_frontend.sh" ]]; then
  echo "Error: run_frontend.sh not found at: ${FRONTEND_DIR}/run_frontend.sh" >&2
  exit 1
fi

# --- setup environments ---
setup_venv "${BACKEND_DIR}" "${BACKEND_DIR}/requirements.txt"
deactivate || true
setup_venv "${FRONTEND_DIR}" "${FRONTEND_DIR}/requirements.txt"
deactivate || true

# --- start backend ---
echo "[run_all] Starting backend..."
( cd "${BACKEND_DIR}" && bash ./run_backend.sh ) &
BACKEND_PID=$!

cleanup() {
  echo
  echo "[run_all] Stopping backend (PID ${BACKEND_PID})..."
  kill "${BACKEND_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Give backend a few seconds to come up
sleep 5

# --- start frontend ---
echo "[run_all] Starting frontend..."
( cd "${FRONTEND_DIR}" && bash ./run_frontend.sh )
