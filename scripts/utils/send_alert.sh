#!/usr/bin/env bash
# =============================================================
# send_alert.sh — Send a message to the configured alert channel
# Default: Telegram via curl
#
# Usage: bash send_alert.sh <message-file>
#
# Reads from environment (loaded via load_env.sh):
#   TELEGRAM_TOKEN    — your Telegram bot token
#   TELEGRAM_CHAT_ID  — your Telegram chat/user ID
# =============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=load_env.sh
source "${SCRIPT_DIR}/load_env.sh"

MESSAGE_FILE="${1:-}"
if [[ -z "$MESSAGE_FILE" || ! -f "$MESSAGE_FILE" ]]; then
    echo "Error: message file not found: ${MESSAGE_FILE:-<none>}"
    exit 1
fi

MESSAGE=$(cat "$MESSAGE_FILE")
TELEGRAM_TOKEN="${TELEGRAM_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

if [[ -z "$TELEGRAM_TOKEN" ]]; then
    echo "Error: TELEGRAM_TOKEN is not set in .env"
    exit 1
fi
if [[ -z "$TELEGRAM_CHAT_ID" ]]; then
    echo "Error: TELEGRAM_CHAT_ID is not set in .env"
    exit 1
fi

curl -s -X POST \
    "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=${MESSAGE}" \
    -d "parse_mode=HTML" > /dev/null

echo "Alert sent."
