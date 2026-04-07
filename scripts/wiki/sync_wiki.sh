#!/usr/bin/env bash
# ChiefOS Wiki — Cloud Sync
# Syncs wiki/ and raw/ to cloud storage (Google Drive, Dropbox, etc.)
# so you can browse your wiki in Obsidian on any device.
#
# Requires rclone: https://rclone.org/install/
# Configure a remote first: rclone config
#
# Usage: bash scripts/wiki/sync_wiki.sh
# Runs automatically via cron if RCLONE_REMOTE is set in config.env.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE=$(find "$SCRIPT_DIR/../.." -maxdepth 1 -name ".env" -o -name "config.env" 2>/dev/null | head -1)
[[ -f "$ENV_FILE" ]] && source "$ENV_FILE"

BASE="${BASE_DIR:-$(pwd)}"
REMOTE="${RCLONE_REMOTE:-}"
CLOUD_PATH="${RCLONE_WIKI_PATH:-}"

if [[ -z "$REMOTE" || -z "$CLOUD_PATH" ]]; then
    echo "RCLONE_REMOTE and RCLONE_WIKI_PATH must be set in config.env"
    echo "Example:"
    echo "  RCLONE_REMOTE=gdrive"
    echo "  RCLONE_WIKI_PATH=MyDrive/ChiefOS"
    exit 1
fi

if ! command -v rclone &>/dev/null; then
    echo "rclone not found. Install with: curl https://rclone.org/install.sh | sudo bash"
    exit 1
fi

WIKI_DIR="$BASE/wiki"
RAW_DIR="$BASE/raw"
TIMESTAMP=$(date +%Y-%m-%dT%H:%M:%S)

echo "[$TIMESTAMP] Syncing wiki to $REMOTE:$CLOUD_PATH/wiki/"

# Sync wiki/ → cloud (one-way: server is source of truth)
rclone sync "$WIKI_DIR" "$REMOTE:$CLOUD_PATH/wiki/" \
    --include "*.md" \
    --log-level ERROR \
    2>&1

# Sync raw/ → cloud (so you can browse source files in Obsidian)
if [[ -d "$RAW_DIR" ]]; then
    rclone sync "$RAW_DIR" "$REMOTE:$CLOUD_PATH/raw/" \
        --log-level ERROR \
        2>&1
fi

echo "[$TIMESTAMP] Sync complete → $REMOTE:$CLOUD_PATH/"
