#!/usr/bin/env bash
set -euo pipefail

# Always operate relative to this file's folder (scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"

# Sanity checks
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

echo "[run_all] Starting frontend..."
( cd "${FRONTEND_DIR}" && bash ./run_frontend.sh )
