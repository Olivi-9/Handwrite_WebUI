#!/bin/sh
set -e

# Container entrypoint: plain HTTP only. Public access goes through
# Cloudflare Tunnel, which terminates TLS in front of this service.

HOST="${BACKEND_HOST:-0.0.0.0}"
PORT="${BACKEND_PORT:-8000}"

echo "Starting backend HTTP server on ${HOST}:${PORT}"

exec uvicorn backend.main:app \
    --host "$HOST" \
    --port "$PORT"
