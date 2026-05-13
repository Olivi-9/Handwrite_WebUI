#!/bin/sh
set -e

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BACKEND_PROJECT_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"

# shellcheck disable=SC1091
. "${SCRIPT_DIR}/backend_common.sh"

backend_load_env

HOST="$(backend_first_non_empty "${BACKEND_HOST:-}" "0.0.0.0")"
PORT="$(backend_first_non_empty "${BACKEND_PORT:-}" "8443")"
DOMAIN="$(backend_primary_domain "$(backend_first_non_empty "${BACKEND_DOMAIN:-}" "${LETSENCRYPT_DOMAIN:-}" "localhost")")"

VENV_DIR="$(backend_abspath "$(backend_first_non_empty "${BACKEND_VENV_DIR:-}" "./.venv")")"
LETSENCRYPT_DIR="$(backend_abspath "$(backend_first_non_empty "${LETSENCRYPT_DIR:-}" "./certs/letsencrypt")")"
LOCAL_CERT_DIR="$(backend_abspath "$(backend_first_non_empty "${LOCAL_CERT_DIR:-}" "./certs/local")")"
LOCAL_CERT_FILE="$(backend_abspath "$(backend_first_non_empty "${LOCAL_CERT_FILE:-}" "${LOCAL_CERT_DIR}/localhost.crt")")"
LOCAL_KEY_FILE="$(backend_abspath "$(backend_first_non_empty "${LOCAL_KEY_FILE:-}" "${LOCAL_CERT_DIR}/localhost.key")")"
LE_CERT_FILE="${LETSENCRYPT_DIR}/live/${DOMAIN}/fullchain.pem"
LE_KEY_FILE="${LETSENCRYPT_DIR}/live/${DOMAIN}/privkey.pem"
MANUAL_CERT_FILE_RAW="$(backend_first_non_empty "${BACKEND_SSL_CERT_FILE:-}" "${SSL_CERT_FILE:-}" "")"
MANUAL_KEY_FILE_RAW="$(backend_first_non_empty "${BACKEND_SSL_KEY_FILE:-}" "${SSL_KEY_FILE:-}" "")"

unset SSL_CERT_FILE SSL_KEY_FILE

# Certificate resolution: manual -> Let's Encrypt -> local. No auto-generation.
CERT_SOURCE=""

if [ -n "$MANUAL_CERT_FILE_RAW" ] && [ -n "$MANUAL_KEY_FILE_RAW" ]; then
    MANUAL_CERT_FILE="$(backend_abspath "$MANUAL_CERT_FILE_RAW")"
    MANUAL_KEY_FILE="$(backend_abspath "$MANUAL_KEY_FILE_RAW")"
    if [ -f "$MANUAL_CERT_FILE" ] && [ -f "$MANUAL_KEY_FILE" ]; then
        CERT_FILE="$MANUAL_CERT_FILE"
        KEY_FILE="$MANUAL_KEY_FILE"
        CERT_SOURCE="manual"
    else
        echo "ERROR: BACKEND_SSL_CERT_FILE/BACKEND_SSL_KEY_FILE were set but the files do not exist:" >&2
        echo "  cert: $MANUAL_CERT_FILE" >&2
        echo "  key:  $MANUAL_KEY_FILE" >&2
        exit 1
    fi
fi

if [ -z "$CERT_SOURCE" ] && [ -f "$LE_CERT_FILE" ] && [ -f "$LE_KEY_FILE" ]; then
    CERT_FILE="$LE_CERT_FILE"
    KEY_FILE="$LE_KEY_FILE"
    CERT_SOURCE="letsencrypt"
fi

if [ -z "$CERT_SOURCE" ] && [ -f "$LOCAL_CERT_FILE" ] && [ -f "$LOCAL_KEY_FILE" ]; then
    CERT_FILE="$LOCAL_CERT_FILE"
    KEY_FILE="$LOCAL_KEY_FILE"
    CERT_SOURCE="local"
fi

if [ -z "$CERT_SOURCE" ]; then
    echo "ERROR: no HTTPS certificate found." >&2
    echo "Looked for, in priority order:" >&2
    echo "  1. Manual:        BACKEND_SSL_CERT_FILE / BACKEND_SSL_KEY_FILE (not set or files missing)" >&2
    echo "  2. Let's Encrypt: $LE_CERT_FILE" >&2
    echo "                    $LE_KEY_FILE" >&2
    echo "  3. Local:         $LOCAL_CERT_FILE" >&2
    echo "                    $LOCAL_KEY_FILE" >&2
    echo "" >&2
    echo "Resolve by one of:" >&2
    echo "  - Run ./scripts/backend_issue_cert.sh --domain <domain> --email <email>" >&2
    echo "  - Place your own certificate at the local paths above" >&2
    echo "  - Export BACKEND_SSL_CERT_FILE and BACKEND_SSL_KEY_FILE" >&2
    exit 1
fi

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

echo "Starting backend HTTPS server on ${HOST}:${PORT}"
echo "Project root: ${BACKEND_PROJECT_ROOT}"
echo "Python:       ${PYTHON_BIN}"
echo "Certificate:  ${CERT_FILE} (${CERT_SOURCE})"
echo "Private key:  ${KEY_FILE}"

exec "$PYTHON_BIN" -m uvicorn backend.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --ssl-certfile "$CERT_FILE" \
    --ssl-keyfile "$KEY_FILE"
