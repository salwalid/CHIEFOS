#!/usr/bin/env bash
# =============================================================
# load_env.sh — Load ChiefOS environment variables from .env
#
# Source this file from any script:
#   source "$(dirname "$0")/../load_env.sh"     (from core/ or alerts/)
#   source "$(dirname "$0")/load_env.sh"        (from utils/)
#
# The .env file lives at $BASE_DIR/.env
# BASE_DIR defaults to the parent of the scripts/ directory.
# =============================================================

# Resolve BASE_DIR from file location if not already set
if [[ -z "${BASE_DIR:-}" ]]; then
    _LOAD_ENV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    BASE_DIR="$(cd "${_LOAD_ENV_DIR}/../.." && pwd)"
fi

ENV_FILE="${BASE_DIR}/.env"

if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "$ENV_FILE"
    set +a
else
    echo "Warning: .env not found at ${ENV_FILE}" >&2
    echo "  Copy config.env.template to ${BASE_DIR}/.env and fill in your values." >&2
fi
