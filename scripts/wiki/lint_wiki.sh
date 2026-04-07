#!/usr/bin/env bash
# ChiefOS Wiki — Linter
# Finds orphan pages, broken links, oversized hot.md, pages missing from index.
# Usage: bash scripts/wiki/lint_wiki.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE=$(find "$SCRIPT_DIR/../.." -maxdepth 1 -name ".env" -o -name "config.env" 2>/dev/null | head -1)
[[ -f "$ENV_FILE" ]] && source "$ENV_FILE"

WIKI_DIR="${BASE_DIR:-$(pwd)}/wiki"
HOT_MD="$WIKI_DIR/hot.md"
INDEX_MD="$WIKI_DIR/index.md"
LOG_MD="$WIKI_DIR/log.md"
TODAY=$(date +%Y-%m-%d)
ISSUES=0

echo "=== ChiefOS Wiki Lint — $TODAY ==="
echo ""

if [[ ! -d "$WIKI_DIR" ]]; then
    echo "❌ Wiki not found at $WIKI_DIR"
    exit 1
fi

PAGE_COUNT=$(find "$WIKI_DIR" -name "*.md" ! -name "index.md" ! -name "log.md" ! -name "hot.md" | wc -l)
echo "Pages in wiki: $PAGE_COUNT"
echo ""

# --- Orphan pages (no inbound links) ---
echo "--- Orphan Pages ---"
ORPHANS=0
find "$WIKI_DIR" -name "*.md" ! -name "index.md" ! -name "log.md" ! -name "hot.md" | while read -r page; do
    slug=$(basename "$page" .md)
    inbound=$(grep -rl "\[\[$slug\]\]" "$WIKI_DIR" --include="*.md" 2>/dev/null | grep -v "$page" | wc -l || echo 0)
    if [[ "$inbound" -eq 0 ]]; then
        echo "  ⚠️  ${page#$WIKI_DIR/}"
        ORPHANS=$((ORPHANS + 1))
    fi
done
[[ "$ORPHANS" -eq 0 ]] && echo "  ✅ None"
ISSUES=$((ISSUES + ORPHANS))

# --- Broken internal links ---
echo ""
echo "--- Broken Internal Links ---"
BROKEN=0
grep -rh "\[\[.*\]\]" "$WIKI_DIR" --include="*.md" 2>/dev/null | \
    grep -oP '\[\[\K[^\]]+(?=\]\])' | sort -u | while read -r link; do
    slug=$(echo "$link" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g')
    if ! find "$WIKI_DIR" -name "${slug}.md" 2>/dev/null | grep -q .; then
        echo "  ⚠️  [[$link]] — no matching page"
        BROKEN=$((BROKEN + 1))
    fi
done
[[ "$BROKEN" -eq 0 ]] && echo "  ✅ None"
ISSUES=$((ISSUES + BROKEN))

# --- hot.md size check ---
echo ""
echo "--- Hot Cache ---"
if [[ -f "$HOT_MD" ]]; then
    LINE_COUNT=$(wc -l < "$HOT_MD")
    if [[ "$LINE_COUNT" -gt 500 ]]; then
        echo "  ⚠️  hot.md is $LINE_COUNT lines — trim to 500 (keep most recent)"
        ISSUES=$((ISSUES + 1))
    else
        echo "  ✅ hot.md: $LINE_COUNT / 500 lines"
    fi
else
    echo "  ⚠️  hot.md missing"
    ISSUES=$((ISSUES + 1))
fi

# --- Pages missing from index ---
echo ""
echo "--- Not Listed in Index ---"
MISSING=0
find "$WIKI_DIR" -name "*.md" ! -name "index.md" ! -name "log.md" ! -name "hot.md" | while read -r page; do
    rel="${page#$WIKI_DIR/}"
    slug=$(basename "$page" .md)
    if ! grep -qi "\[\[$slug\]\]\|$rel" "$INDEX_MD" 2>/dev/null; then
        echo "  ⚠️  $rel"
        MISSING=$((MISSING + 1))
    fi
done
[[ "$MISSING" -eq 0 ]] && echo "  ✅ All pages indexed"
ISSUES=$((ISSUES + MISSING))

# --- Summary ---
echo ""
echo "=== Summary ==="
if [[ "$ISSUES" -eq 0 ]]; then
    echo "✅ Wiki is healthy — no issues found"
else
    echo "⚠️  $ISSUES issue(s) found — review above"
fi

# Append to log
echo "" >> "$LOG_MD"
echo "## [$TODAY] lint | $ISSUES issue(s) | $PAGE_COUNT pages" >> "$LOG_MD"
echo ""
echo "Logged to wiki/log.md"
