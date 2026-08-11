#!/bin/sh
set -e

# Starts the backend over plain HTTP. TLS is terminated upstream by
# Cloudflare Tunnel (cloudflared), so no certificate is needed here.

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BACKEND_PROJECT_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"

# shellcheck disable=SC1091
. "${SCRIPT_DIR}/backend_common.sh"

backend_load_env

HOST="$(backend_first_non_empty "${BACKEND_HOST:-}" "127.0.0.1")"
PORT="$(backend_first_non_empty "${BACKEND_PORT:-}" "8000")"
VENV_DIR="$(backend_abspath "$(backend_first_non_empty "${BACKEND_VENV_DIR:-}" "./.venv")")"

if [ -x "${VENV_DIR}/bin/python" ]; then
    PYTHON_BIN="${VENV_DIR}/bin/python"
else
    PYTHON_BIN="$(command -v python3 || true)"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: python3 is not installed." >&2
    exit 1
fi

if ! "$PYTHON_BIN" -c "import fastapi, uvicorn, PIL" >/dev/null 2>&1; then
    echo "ERROR: backend dependencies are not installed for $PYTHON_BIN." >&2
    echo "Install them via: pip install -r requirements.txt (or 'uv pip install -r requirements.txt')." >&2
    exit 1
fi

cd "$BACKEND_PROJECT_ROOT"

echo "Starting backend HTTP server on ${HOST}:${PORT}"
echo "Project root: ${BACKEND_PROJECT_ROOT}"
echo "Python:       ${PYTHON_BIN}"

exec "$PYTHON_BIN" -m uvicorn backend.main:app \
    --host "$HOST" \
    --port "$PORT"
