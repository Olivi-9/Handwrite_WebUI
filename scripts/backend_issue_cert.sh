#!/bin/sh
set -e

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BACKEND_PROJECT_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"

# shellcheck disable=SC1091
. "${SCRIPT_DIR}/backend_common.sh"

backend_load_env

DOMAIN="$(backend_first_non_empty "${BACKEND_DOMAIN:-}" "${LETSENCRYPT_DOMAIN:-}" "")"
EMAIL="$(backend_first_non_empty "${LETSENCRYPT_EMAIL:-}" "")"
WEBROOT_RAW="$(backend_first_non_empty "${CERTBOT_WEBROOT:-}" "")"
OUTPUT_DIR="$(backend_abspath "$(backend_first_non_empty "${LETSENCRYPT_DIR:-}" "./certs/letsencrypt")")"
MODE="webroot"
STAGING="false"
NGINX_ACME_CONF="/etc/nginx/conf.d/handwrite-backend-acme.conf"

is_bool_word() {
    case "$1" in
        true|false|1|0|yes|no|on|off)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

print_help() {
    cat <<EOF
Usage: $0 [--domain <your-domain>] [--email <your-email>] [--webroot <path>] [--output <path>] [--mode webroot|standalone] [--staging]

Defaults:
  --domain   BACKEND_DOMAIN or LETSENCRYPT_DOMAIN from .env / .env.backend.local
  --email    LETSENCRYPT_EMAIL from .env / .env.backend.local
  --webroot  ./certs/www
  --output   ./certs/letsencrypt

Options:
  --domain       证书域名，可逗号分隔多个域名。
  --email        Let's Encrypt 邮箱（用于到期通知）。
  --webroot      webroot 路径，适用于 HTTP-01 验证。
  --output       证书输出目录。
  --mode         webroot（默认）或 standalone。
  --staging      使用 Let's Encrypt staging 环境，避免触发正式限额。
  -h, --help     显示本帮助。
EOF
}

resolve_default_webroot() {
    if [ -n "$WEBROOT_RAW" ]; then
        backend_abspath "$WEBROOT_RAW"
        return 0
    fi

    if [ "$(id -u)" = "0" ] && command -v nginx >/dev/null 2>&1; then
        printf '%s\n' "/var/www/certbot"
        return 0
    fi

    backend_abspath "./certs/www"
}

render_nginx_acme_config() {
    server_names=""

    OLD_IFS="$IFS"
    IFS=','
    for raw_domain in $DOMAIN; do
        item="$(backend_trim "$raw_domain")"
        [ -z "$item" ] && continue
        server_names="${server_names} ${item}"
    done
    IFS="$OLD_IFS"

    server_names="$(backend_trim "$server_names")"
    if [ -z "$server_names" ]; then
        echo "ERROR: unable to derive nginx server_name values from domain list." >&2
        exit 1
    fi

    cat > "$NGINX_ACME_CONF" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${server_names};

    location ^~ /.well-known/acme-challenge/ {
        default_type "text/plain";
        root ${WEBROOT};
        try_files \$uri =404;
    }

    location / {
        return 404;
    }
}
EOF
}

ensure_nginx_webroot_route() {
    if ! command -v nginx >/dev/null 2>&1; then
        echo "ERROR: nginx is required for webroot mode on this machine." >&2
        echo "Install nginx or rerun with --mode standalone." >&2
        exit 1
    fi

    if [ "$(id -u)" != "0" ]; then
        echo "ERROR: root privileges are required to manage nginx for webroot mode." >&2
        echo "Rerun as root, or use --mode standalone." >&2
        exit 1
    fi

    mkdir -p "$WEBROOT"
    chmod 755 "$WEBROOT"

    render_nginx_acme_config

    nginx -t
    if pgrep -x nginx >/dev/null 2>&1; then
        nginx -s reload
    else
        nginx
    fi
}

verify_webroot_serving() {
    probe_name="handwrite-probe-$$"
    probe_path="${WEBROOT}/.well-known/acme-challenge/${probe_name}"
    probe_url="http://127.0.0.1/.well-known/acme-challenge/${probe_name}"
    expected_body="ok-${probe_name}"

    mkdir -p "${WEBROOT}/.well-known/acme-challenge"
    printf '%s\n' "$expected_body" > "$probe_path"
    chmod 644 "$probe_path"

    probe_ok="false"
    retries=0
    while [ "$retries" -lt 10 ]; do
        retries=$((retries + 1))

        OLD_IFS="$IFS"
        IFS=','
        for raw_domain in $DOMAIN; do
            item="$(backend_trim "$raw_domain")"
            [ -z "$item" ] && continue
            response="$(curl -fsS -H "Host: ${item}" "$probe_url" 2>/dev/null || true)"
            if [ "$response" = "$expected_body" ]; then
                probe_ok="true"
                break
            fi
        done
        IFS="$OLD_IFS"

        [ "$probe_ok" = "true" ] && break
        sleep 1
    done

    rm -f "$probe_path"

    if [ "$probe_ok" != "true" ]; then
        echo "ERROR: nginx is not serving ACME challenge files from ${WEBROOT}." >&2
        echo "Checked URL: ${probe_url}" >&2
        echo "Expected body: ${expected_body}" >&2
        echo "Please ensure the domain points to this server and that port 80 is reachable." >&2
        exit 1
    fi
}

while [ $# -gt 0 ]; do
    case "$1" in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --email)
            EMAIL="$2"
            shift 2
            ;;
        --webroot)
            WEBROOT="$(backend_abspath "$2")"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$(backend_abspath "$2")"
            shift 2
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --staging)
            if [ $# -gt 1 ] && is_bool_word "$2"; then
                STAGING="$(backend_bool "$2")"
                shift 2
            else
                STAGING="true"
                shift 1
            fi
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

DOMAIN="$(backend_trim "$DOMAIN")"
EMAIL="$(backend_trim "$EMAIL")"
WEBROOT="$(resolve_default_webroot)"

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "ERROR: domain and email are required." >&2
    echo "You can pass --domain/--email, or set BACKEND_DOMAIN/LETSENCRYPT_DOMAIN and LETSENCRYPT_EMAIL in .env." >&2
    exit 1
fi

if [ "$MODE" != "webroot" ] && [ "$MODE" != "standalone" ]; then
    echo "ERROR: --mode must be either webroot or standalone." >&2
    exit 1
fi

if ! command -v certbot >/dev/null 2>&1; then
    echo "ERROR: certbot is not installed." >&2
    echo "Install certbot first, then rerun this script." >&2
    exit 1
fi

CONFIG_DIR="$OUTPUT_DIR"
WORK_DIR="$OUTPUT_DIR/work"
LOGS_DIR="$OUTPUT_DIR/logs"

mkdir -p "$WEBROOT" "$CONFIG_DIR" "$WORK_DIR" "$LOGS_DIR"

DOMAIN_ARGS=""
OLD_IFS="$IFS"
IFS=','
for raw_domain in $DOMAIN; do
    item="$(backend_trim "$raw_domain")"
    [ -z "$item" ] && continue
    DOMAIN_ARGS="${DOMAIN_ARGS} -d ${item}"
done
IFS="$OLD_IFS"

if [ -z "$DOMAIN_ARGS" ]; then
    echo "ERROR: invalid domain list: $DOMAIN" >&2
    exit 1
fi

PRIMARY_DOMAIN="$(backend_primary_domain "$DOMAIN")"

COMMON_ARGS="--non-interactive --agree-tos --email $EMAIL --config-dir $CONFIG_DIR --work-dir $WORK_DIR --logs-dir $LOGS_DIR"
if [ "$STAGING" = "true" ]; then
    COMMON_ARGS="${COMMON_ARGS} --staging"
fi

if [ "$MODE" = "standalone" ]; then
    echo "Requesting certificate in standalone mode for: $DOMAIN"
    # shellcheck disable=SC2086
    certbot certonly --standalone $COMMON_ARGS $DOMAIN_ARGS
else
    echo "Requesting certificate in webroot mode for: $DOMAIN"
    echo "Using webroot: $WEBROOT"
    ensure_nginx_webroot_route
    verify_webroot_serving
    # shellcheck disable=SC2086
    certbot certonly --webroot -w "$WEBROOT" --keep-until-expiring $COMMON_ARGS $DOMAIN_ARGS
fi

CRT_PATH="$CONFIG_DIR/live/$PRIMARY_DOMAIN/fullchain.pem"
KEY_PATH="$CONFIG_DIR/live/$PRIMARY_DOMAIN/privkey.pem"
CHAIN_PATH="$CONFIG_DIR/live/$PRIMARY_DOMAIN/chain.pem"

if [ ! -f "$CRT_PATH" ] || [ ! -f "$KEY_PATH" ]; then
    echo "ERROR: certificate generation did not produce the expected files." >&2
    exit 2
fi

cat <<EOF
Certificate ready:
  fullchain: $CRT_PATH
  privkey:   $KEY_PATH
  chain:     $CHAIN_PATH

You can now start the backend with:
  BACKEND_SSL_CERT_FILE=$CRT_PATH BACKEND_SSL_KEY_FILE=$KEY_PATH ./scripts/run_backend_https.sh
EOF
