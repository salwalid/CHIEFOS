#!/usr/bin/env bash
# ChiefOS Wiki — Scaffold a new page
# Usage: bash scripts/wiki/new_page.sh "<title>" <category>
# Categories: research | concepts | entities | topics

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE=$(find "$SCRIPT_DIR/../.." -maxdepth 1 -name ".env" -o -name "config.env" 2>/dev/null | head -1)
[[ -f "$ENV_FILE" ]] && source "$ENV_FILE"

WIKI_DIR="${BASE_DIR:-$(pwd)}/wiki"
TITLE="${1:-}"
CATEGORY="${2:-research}"
TODAY=$(date +%Y-%m-%d)

if [[ -z "$TITLE" ]]; then
    echo "Usage: new_page.sh \"<title>\" <category>"
    echo "Categories: research | concepts | entities | topics"
    exit 1
fi

# Slugify title → filename
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g' | sed 's/--*/-/g' | sed 's/^-\|-$//g')
PAGE_DIR="$WIKI_DIR/$CATEGORY"
PAGE_PATH="$PAGE_DIR/${SLUG}.md"

mkdir -p "$PAGE_DIR"

if [[ -f "$PAGE_PATH" ]]; then
    echo "Page already exists: ${PAGE_PATH#$WIKI_DIR/}"
    exit 0
fi

cat > "$PAGE_PATH" << TEMPLATE
---
title: $TITLE
category: $CATEGORY
created: $TODAY
updated: $TODAY
sources: []
tags: []
---

# $TITLE

<!-- Write content here. Use [[page-name]] for internal wiki links. -->

## Overview


## Key Points


## Related

-
TEMPLATE

echo "✅ Created: ${PAGE_PATH#$WIKI_DIR/}"
echo "   Path: $PAGE_PATH"
