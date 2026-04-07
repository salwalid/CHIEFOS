#!/usr/bin/env bash
# =============================================================
# ChiefOS Wiki — Standalone Installer
# Adds the wiki knowledge base to an existing ChiefOS or
# OpenClaw installation without a full reinstall.
#
# Usage: bash wiki-install.sh
# Run from the CHIEFOS repo directory.
# =============================================================

set -euo pipefail

CHIEFOS_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS="✅"
WARN="⚠️ "
FAIL="❌"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║      ChiefOS Wiki — Standalone Setup     ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# -------------------------------------------------------
# Load config
# -------------------------------------------------------
CONFIG_FILE="$CHIEFOS_SRC/config.env"
ENV_FILE=""

if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
    echo "${PASS} Config loaded from $CONFIG_FILE"
elif [[ -n "${BASE_DIR:-}" && -f "$BASE_DIR/.env" ]]; then
    source "$BASE_DIR/.env"
    ENV_FILE="$BASE_DIR/.env"
    echo "${PASS} Config loaded from $BASE_DIR/.env"
else
    echo "${FAIL} No config found."
    echo "  Option 1: Run from the CHIEFOS directory (config.env present)"
    echo "  Option 2: Set BASE_DIR manually: BASE_DIR=/path/to/install bash wiki-install.sh"
    exit 1
fi

[[ -z "${BASE_DIR:-}" ]] && echo "${FAIL} BASE_DIR not set" && exit 1
[[ -z "${COS_USER:-}" ]] && echo "${FAIL} COS_USER not set" && exit 1

echo ""
echo "  Installing wiki into: $BASE_DIR"
echo "  ChiefOS user:         $COS_USER"
echo ""

# -------------------------------------------------------
# Create wiki directory structure
# -------------------------------------------------------
echo "--- Creating directories ---"
sudo -u "$COS_USER" mkdir -p \
    "$BASE_DIR/wiki/research" \
    "$BASE_DIR/wiki/concepts" \
    "$BASE_DIR/wiki/entities" \
    "$BASE_DIR/wiki/topics" \
    "$BASE_DIR/raw"
echo "${PASS} Directories created"

# -------------------------------------------------------
# Seed wiki files (skip if already present)
# -------------------------------------------------------
echo ""
echo "--- Seeding wiki files ---"
for seed_file in index.md log.md hot.md; do
    DEST="$BASE_DIR/wiki/$seed_file"
    if [[ -f "$DEST" ]]; then
        echo "${WARN} $seed_file already exists — skipping (preserving existing wiki)"
    else
        sudo -u "$COS_USER" cp "$CHIEFOS_SRC/setup/wiki/$seed_file" "$DEST"
        echo "${PASS} $seed_file created"
    fi
done

# -------------------------------------------------------
# Deploy wiki scripts
# -------------------------------------------------------
echo ""
echo "--- Deploying wiki scripts ---"
sudo cp -r "$CHIEFOS_SRC/scripts/wiki/." "$BASE_DIR/scripts/wiki/" 2>/dev/null || \
    sudo mkdir -p "$BASE_DIR/scripts/wiki" && sudo cp -r "$CHIEFOS_SRC/scripts/wiki/." "$BASE_DIR/scripts/wiki/"
sudo find "$BASE_DIR/scripts/wiki" -name "*.sh" -exec chmod +x {} \;
sudo chown -R "$COS_USER:$COS_USER" "$BASE_DIR/scripts/wiki"
echo "${PASS} Wiki scripts deployed"

# -------------------------------------------------------
# Patch AGENTS.md with wiki workflow (if not already patched)
# -------------------------------------------------------
echo ""
echo "--- Patching AGENTS.md ---"
AGENTS_FILE="$BASE_DIR/AGENTS.md"
if [[ -f "$AGENTS_FILE" ]]; then
    if grep -q "## Wiki" "$AGENTS_FILE" 2>/dev/null; then
        echo "${WARN} AGENTS.md already has wiki section — skipping"
    else
        sudo -u "$COS_USER" bash -c "cat '$CHIEFOS_SRC/config/AGENTS_template.md' | grep -A 9999 '## Wiki' >> '$AGENTS_FILE'"
        echo "${PASS} Wiki workflow appended to AGENTS.md"
    fi
else
    echo "${WARN} AGENTS.md not found at $AGENTS_FILE — copy manually from $CHIEFOS_SRC/config/AGENTS_template.md"
fi

# -------------------------------------------------------
# Patch TOOLS.md with wiki paths (if not already patched)
# -------------------------------------------------------
echo ""
echo "--- Patching TOOLS.md ---"
TOOLS_FILE="$BASE_DIR/TOOLS.md"
if [[ -f "$TOOLS_FILE" ]]; then
    if grep -q "wiki_dir" "$TOOLS_FILE" 2>/dev/null; then
        echo "${WARN} TOOLS.md already has wiki section — skipping"
    else
        sudo -u "$COS_USER" bash -c "cat '$CHIEFOS_SRC/config/TOOLS_template.md' | grep -A 9999 '## Wiki Knowledge Base' >> '$TOOLS_FILE'"
        echo "${PASS} Wiki paths appended to TOOLS.md"
    fi
else
    echo "${WARN} TOOLS.md not found at $TOOLS_FILE — copy manually"
fi

# -------------------------------------------------------
# Summary
# -------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║         Wiki Setup Complete!             ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Wiki:     $BASE_DIR/wiki/"
echo "  Raw drop: $BASE_DIR/raw/"
echo "  Index:    $BASE_DIR/wiki/index.md"
echo ""
echo "How to use:"
echo "  1. Drop a file into $BASE_DIR/raw/"
echo "  2. Run: bash $BASE_DIR/scripts/wiki/ingest_prep.sh <filename>"
echo "  3. Tell your agent: 'Ingest $BASE_DIR/raw/<filename> into the wiki'"
echo "  4. Search: bash $BASE_DIR/scripts/wiki/search_wiki.sh <query>"
echo "  5. Lint:   bash $BASE_DIR/scripts/wiki/lint_wiki.sh"
echo ""
