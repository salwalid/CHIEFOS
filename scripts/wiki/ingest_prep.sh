#!/usr/bin/env bash
# ChiefOS Wiki — Ingest Prep
# Previews a raw file and logs the ingest start to wiki/log.md.
# Usage: bash scripts/wiki/ingest_prep.sh <filename-in-raw/>

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE=$(find "$SCRIPT_DIR/../.." -maxdepth 1 -name ".env" -o -name "config.env" 2>/dev/null | head -1)
[[ -f "$ENV_FILE" ]] && source "$ENV_FILE"

BASE="${BASE_DIR:-$(pwd)}"
RAW_DIR="$BASE/raw"
LOG_MD="$BASE/wiki/log.md"
FILENAME="${1:-}"
TODAY=$(date +%Y-%m-%d)

if [[ -z "$FILENAME" ]]; then
    echo "Usage: ingest_prep.sh <filename>"
    echo ""
    echo "Files available in raw/:"
    ls "$RAW_DIR" 2>/dev/null || echo "  (empty)"
    exit 1
fi

RAW_FILE="$RAW_DIR/$FILENAME"
if [[ ! -f "$RAW_FILE" ]]; then
    echo "File not found: $RAW_FILE"
    echo ""
    echo "Files in raw/:"
    ls "$RAW_DIR" 2>/dev/null || echo "  (empty)"
    exit 1
fi

WORDS=$(wc -w < "$RAW_FILE")
LINES=$(wc -l < "$RAW_FILE")

echo "=== Ingest Preview ==="
echo "File:  $FILENAME"
echo "Words: $WORDS | Lines: $LINES"
echo ""
echo "--- First 40 lines ---"
head -40 "$RAW_FILE"
echo "---"
echo ""

# Log to wiki/log.md
echo "" >> "$LOG_MD"
echo "## [$TODAY] ingest | $FILENAME | ${WORDS} words" >> "$LOG_MD"

echo "✅ Logged to wiki/log.md"
echo ""
echo "Next: ask your agent — 'Ingest $RAW_DIR/$FILENAME into the wiki'"
