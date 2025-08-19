#!/usr/bin/env bash
set -euo pipefail

# cd into frontend
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

VENV_DIR=".venv"
POSIX_PY="${VENV_DIR}/bin/python"
WIN_PY="${VENV_DIR}/Scripts/python.exe"

# ensure venv + pick python
if [[ -x "${POSIX_PY}" ]]; then
  PY="${POSIX_PY}"
elif [[ -x "${WIN_PY}" ]]; then
  PY="${WIN_PY}"
else
  python -m venv "${VENV_DIR}"
  if [[ -x "${POSIX_PY}" ]]; then PY="${POSIX_PY}"
  elif [[ -x "${WIN_PY}" ]]; then PY="${WIN_PY}"
  else echo "Error: venv python not found." >&2; exit 1; fi
fi

# install requirements only if changed
REQ_FILE="requirements.txt"
HASH_FILE="${VENV_DIR}/.req_hash"
PIP_MARK="${VENV_DIR}/.pip_upgraded"
REQ_HASH="$("${PY}" - <<'PY' "$REQ_FILE"
import pathlib, hashlib, sys
p=sys.argv[1]; print(hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest())
PY
)"
if [[ ! -f "${PIP_MARK}" ]]; then
  "${PY}" -m pip install --upgrade pip
  touch "${PIP_MARK}"
fi
if [[ ! -f "${HASH_FILE}" || "$(cat "${HASH_FILE}")" != "${REQ_HASH}" ]]; then
  echo "[frontend] Installing / updating dependencies..."
  "${PY}" -m pip install -r "${REQ_FILE}"
  echo "${REQ_HASH}" > "${HASH_FILE}"
else
  echo "[frontend] Requirements unchanged; skipping pip install."
fi

# sanity check
if [[ ! -f "app.py" ]]; then
  echo "Error: frontend/app.py not found." >&2
  exit 1
fi

# run Streamlit
exec "${PY}" -m streamlit run app.py --server.port=8501 --server.address=127.0.0.1
