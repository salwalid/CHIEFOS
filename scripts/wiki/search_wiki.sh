#!/usr/bin/env bash
# ChiefOS Wiki — Search
# Usage: bash scripts/wiki/search_wiki.sh <query>
# Searches all wiki pages for matching content.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE=$(find "$SCRIPT_DIR/../.." -maxdepth 1 -name ".env" -o -name "config.env" 2>/dev/null | head -1)
[[ -f "$ENV_FILE" ]] && source "$ENV_FILE"

WIKI_DIR="${BASE_DIR:-$(pwd)}/wiki"
QUERY="${1:-}"

if [[ -z "$QUERY" ]]; then
    echo "Usage: search_wiki.sh <query>"
    exit 1
fi

if [[ ! -d "$WIKI_DIR" ]]; then
    echo "Wiki not found at $WIKI_DIR — has ChiefOS been installed?"
    exit 1
fi

RESULTS=$(grep -ril "$QUERY" "$WIKI_DIR" --include="*.md" 2>/dev/null || true)

if [[ -z "$RESULTS" ]]; then
    echo "No results for: $QUERY"
    exit 0
fi

echo "Results for: \"$QUERY\""
echo "---"
echo "$RESULTS" | while read -r file; do
    echo ""
    echo "📄 ${file#$WIKI_DIR/}"
    grep -n -i "$QUERY" "$file" | head -5 | sed 's/^/   /'
done
