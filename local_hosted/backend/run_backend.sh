# #!/usr/bin/env bash
# set -euo pipefail

# VENV_DIR=".venv"
# POSIX_PY="${VENV_DIR}/bin/python"
# WIN_PY="${VENV_DIR}/Scripts/python.exe"

# # --- ensure venv + get venv python ---
# if [[ -x "${POSIX_PY}" ]]; then
#   PY="${POSIX_PY}"
# elif [[ -x "${WIN_PY}" ]]; then
#   PY="${WIN_PY}"
# else
#   python -m venv "${VENV_DIR}"
#   if [[ -x "${POSIX_PY}" ]]; then
#     PY="${POSIX_PY}"
#   elif [[ -x "${WIN_PY}" ]]; then
#     PY="${WIN_PY}"
#   else
#     echo "Error: could not locate venv python." >&2
#     exit 1
#   fi
# fi

# # Load optional .env (local to this process only)
# if [[ -f ".env" ]]; then
#   export $(grep -v '^#' .env | xargs) || true
# fi
# PORT="${PORT:-8000}"

# # --- dependency install: only if requirements changed ---
# REQ_FILE="backend/requirements.txt"
# HASH_FILE="${VENV_DIR}/.req_hash"
# PIP_MARK="${VENV_DIR}/.pip_upgraded"

# # Compute SHA-256 of requirements.txt using venv's Python (portable)
# REQ_HASH="$("${PY}" - <<'PY' "$REQ_FILE"
# import hashlib, sys
# p = sys.argv[1]
# h = hashlib.sha256()
# with open(p, 'rb') as f:
#     h.update(f.read())
# print(h.hexdigest())
# PY
# )"

# # Upgrade pip only once per venv (create a marker)
# if [[ ! -f "${PIP_MARK}" ]]; then
#   "${PY}" -m pip install --upgrade pip
#   touch "${PIP_MARK}"
# fi

# # Install deps only if hash changed or hash file missing
# NEED_INSTALL="yes"
# if [[ -f "${HASH_FILE}" ]]; then
#   OLD_HASH="$(cat "${HASH_FILE}")"
#   if [[ "${OLD_HASH}" == "${REQ_HASH}" ]]; then
#     NEED_INSTALL="no"
#   fi
# fi

# if [[ "${NEED_INSTALL}" == "yes" ]]; then
#   echo "[backend] Installing / updating dependencies..."
#   "${PY}" -m pip install -r "${REQ_FILE}"
#   echo "${REQ_HASH}" > "${HASH_FILE}"
# else
#   echo "[backend] Requirements unchanged; skipping pip install."
# fi

# # Optional: verify dependency consistency (non-fatal if missing)
# "${PY}" -m pip check || true

# # Run FastAPI (from venv)
# exec "${PY}" -m uvicorn main:app --reload --host 0.0.0.0 --port "${PORT}"

#!/usr/bin/env bash
set -euo pipefail

# always run from the script's directory (backend/)
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

# optional .env
if [[ -f ".env" ]]; then
  export $(grep -v '^#' .env | xargs) || true
fi
PORT="${PORT:-8000}"

# install deps only if requirements changed (hash cache)
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
  echo "[backend] Installing / updating dependencies..."
  "${PY}" -m pip install -r "${REQ_FILE}"
  echo "${REQ_HASH}" > "${HASH_FILE}"
else
  echo "[backend] Requirements unchanged; skipping pip install."
fi

# sanity check: main.py + app
if [[ ! -f "main.py" ]]; then
  echo "Error: backend/main.py not found." >&2; exit 1
fi
"${PY}" - <<'PY'
import importlib
m=importlib.import_module("main")
assert hasattr(m, "app"), "FastAPI 'app' not found in main.py"
print("Import check OK: main.app")
PY

# run uvicorn from venv, now that we are in backend/
exec "${PY}" -m uvicorn main:app --reload --host 127.0.0.1 --port "${PORT}"
