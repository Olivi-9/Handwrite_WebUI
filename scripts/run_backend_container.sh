#!/bin/sh
set -e

HOST="${BACKEND_HOST:-0.0.0.0}"
PORT="${BACKEND_PORT:-8443}"
LETSENCRYPT_DIR="${LETSENCRYPT_DIR:-/app/certs/letsencrypt}"
LOCAL_CERT_DIR="${LOCAL_CERT_DIR:-/app/certs/local}"

if [ -n "${BACKEND_DOMAIN:-}" ]; then
    DOMAIN="$BACKEND_DOMAIN"
elif [ -n "${LETSENCRYPT_DOMAIN:-}" ]; then
    DOMAIN="$LETSENCRYPT_DOMAIN"
else
    DOMAIN="localhost"
fi

PRIMARY_DOMAIN="$(printf '%s' "$DOMAIN" | cut -d',' -f1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
LE_CERT_FILE="${LETSENCRYPT_DIR}/live/${PRIMARY_DOMAIN}/fullchain.pem"
LE_KEY_FILE="${LETSENCRYPT_DIR}/live/${PRIMARY_DOMAIN}/privkey.pem"
LOCAL_CERT_FILE="${LOCAL_CERT_DIR}/localhost.crt"
LOCAL_KEY_FILE="${LOCAL_CERT_DIR}/localhost.key"

MANUAL_CERT_FILE="${BACKEND_SSL_CERT_FILE:-}"
MANUAL_KEY_FILE="${BACKEND_SSL_KEY_FILE:-}"

CERT_SOURCE=""

if [ -n "$MANUAL_CERT_FILE" ] && [ -n "$MANUAL_KEY_FILE" ]; then
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
    exit 1
fi

echo "Starting backend HTTPS server on ${HOST}:${PORT}"
echo "Certificate:  ${CERT_FILE} (${CERT_SOURCE})"
echo "Private key:  ${KEY_FILE}"

exec uvicorn backend.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --ssl-certfile "$CERT_FILE" \
    --ssl-keyfile "$KEY_FILE"
