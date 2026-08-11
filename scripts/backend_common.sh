#!/bin/sh

if [ -z "${BACKEND_PROJECT_ROOT:-}" ]; then
    BACKEND_PROJECT_ROOT="$(pwd)"
fi

backend_load_env_file() {
    env_file="$1"
    if [ ! -f "$env_file" ]; then
        return 0
    fi

    set -a
    # shellcheck disable=SC1090
    . "$env_file"
    set +a
}

backend_load_env() {
    backend_load_env_file "${BACKEND_PROJECT_ROOT}/.env"
    backend_load_env_file "${BACKEND_PROJECT_ROOT}/.env.backend.local"
}

backend_abspath() {
    target="$1"
    if [ -z "$target" ]; then
        return 1
    fi

    case "$target" in
        /*)
            printf '%s\n' "$target"
            ;;
        *)
            printf '%s\n' "${BACKEND_PROJECT_ROOT}/${target#./}"
            ;;
    esac
}

backend_first_non_empty() {
    for value in "$@"; do
        if [ -n "$value" ]; then
            printf '%s\n' "$value"
            return 0
        fi
    done
    printf '\n'
    return 0
}
