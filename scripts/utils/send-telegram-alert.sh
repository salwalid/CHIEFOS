#!/bin/bash
# send-telegram-alert.sh — Send alert to Telegram via ChiefOS CLI
# Usage: ./send-telegram-alert.sh <message-file>

set -euo pipefail

MESSAGE_FILE="$1"

if [ ! -f "$MESSAGE_FILE" ]; then
    echo "Error: Message file not found: $MESSAGE_FILE"
    exit 1
fi

MESSAGE=$(cat "$MESSAGE_FILE")
TELEGRAM_USER_ID="REDACTED_TELEGRAM_USER_ID"  # User's Telegram ID

# Send via ChiefOS CLI
PATH=$CHIEFOS_HOME/.local/share/pnpm:$PATH /usr/bin/chiefos message send \
    --channel telegram \
    --target "$TELEGRAM_USER_ID" \
    --message "$MESSAGE"

if [ $? -eq 0 ]; then
    echo "Notification sent successfully to Telegram"
else
    echo "Error: Failed to send notification"
    exit 1
fi
