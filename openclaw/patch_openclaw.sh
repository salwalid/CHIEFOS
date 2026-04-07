#!/usr/bin/env bash
# =============================================================
# patch_openclaw.sh — Upgrade an existing OpenClaw workspace
#                     to ChiefOS without breaking agent identity
#
# What this does:
#   1. Backs up existing SOUL.md, TOOLS.md, AGENTS.md
#   2. Appends MaatSpec governance tiers to existing SOUL.md
#      (does NOT replace the identity section — only adds §4–§6)
#   3. Replaces TOOLS.md with ChiefOS DB schema version
#   4. Deploys AGENTS.md if not present (or appends if it exists)
#   5. Deploys scripts/, www/HQ/, and database as net-new
#
# Usage: bash patch_openclaw.sh [openclaw_dir] [chiefos_dir]
#   openclaw_dir: path to existing OpenClaw workspace (default: ~/clawd)
#   chiefos_dir:  path to ChiefOS source (default: current directory)
#
# Run this ONLY if preflight.sh detected an existing OpenClaw workspace.
# =============================================================

set -euo pipefail

PASS="✅"
WARN="⚠️ "
FAIL="❌"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

OPENCLAW_DIR="${1:-$HOME/clawd}"
CHIEFOS_SRC="${2:-.}"

echo ""
echo "=============================="
echo "  OpenClaw Patch"
echo "=============================="
echo "  Source:  $CHIEFOS_SRC"
echo "  Target:  $OPENCLAW_DIR"
echo ""

# -------------------------------------------------------
# Validate
# -------------------------------------------------------
if [[ ! -d "$OPENCLAW_DIR" ]]; then
    echo "${FAIL} OpenClaw directory not found: $OPENCLAW_DIR"
    exit 1
fi

if [[ ! -f "$OPENCLAW_DIR/SOUL.md" ]]; then
    echo "${FAIL} SOUL.md not found at $OPENCLAW_DIR — not a valid OpenClaw workspace"
    exit 1
fi

if [[ ! -f "$CHIEFOS_SRC/config/SOUL_template.md" ]]; then
    echo "${FAIL} ChiefOS source not found at $CHIEFOS_SRC (missing config/SOUL_template.md)"
    exit 1
fi

BACKUP_DIR="$OPENCLAW_DIR/backups/chiefos_patch_$TIMESTAMP"
mkdir -p "$BACKUP_DIR"
echo "  Backups → $BACKUP_DIR"
echo ""

# -------------------------------------------------------
# Step 1 — Back up existing governance files
# -------------------------------------------------------
echo "--- Step 1: Backing up existing files ---"

for f in SOUL.md TOOLS.md AGENTS.md; do
    if [[ -f "$OPENCLAW_DIR/$f" ]]; then
        cp "$OPENCLAW_DIR/$f" "$BACKUP_DIR/${f}.openclaw_backup"
        echo "  ${PASS} Backed up $f"
    fi
done
echo ""

# -------------------------------------------------------
# Step 2 — Patch SOUL.md
# Append MaatSpec §4–§6 if not already present.
# The identity section (§1–§3) is untouched.
# -------------------------------------------------------
echo "--- Step 2: Patching SOUL.md (appending governance tiers) ---"

if grep -q "MaatSpec Tier Matrix" "$OPENCLAW_DIR/SOUL.md" 2>/dev/null; then
    echo "  ${WARN} MaatSpec tiers already present in SOUL.md — skipping"
else
    cat >> "$OPENCLAW_DIR/SOUL.md" << 'MAAT_APPEND'

---
<!-- ChiefOS MaatSpec Governance — appended by patch_openclaw.sh -->

## §4 — MaatSpec Tier Matrix (Reference Only)

The COS Agent classifies actions for its own awareness, but **Angel independently determines whether authorization is required.** The Agent's self-classification does not override Angel's judgment.

**Tiers 1–3 are autonomous.** Angel will return APPROVE/APPROVE:NOTIFY and the Agent proceeds without waiting for Principal authorization.

### Tier 1 — Observe (Autonomous, Silent)
All read operations: files, database SELECT, web search, status checks.

### Tier 2 — Create (Autonomous, Notify)
Additive-only: new files, INSERT into tables, drafts, log entries, backups, new cron jobs.

### Tier 3 — Operate (Autonomous, Notify)
Reversible internal modifications: UPDATE records, edit operational files, run known scripts, internal agent routing, file moves, deploy to existing endpoints, modify cron schedules.

### Tier 4 — Consequential (Explicit Auth)
Destructive, external, bulk, or hard-to-reverse: DELETE operations, external comms, new/untested scripts, bulk ops (>10 records or >5 files), financial transactions, infrastructure changes, overwrites without backup.

### Tier 5 — Constitutional (Explicit Unlock)
Governance framework modifications: SOUL files, AGENTS.md, credentials, tier definitions.

## §5 — Guardian Protocol

The Guardian is an external MCP tool (`angel.verify_action_plan`). Every action beyond Tier 1 must be submitted before execution.

**Submission:**
Call `angel.verify_action_plan` with: `action`, `auth` (Principal phrase or NONE), `msg` (message_id or NONE), `transcript_snapshot` (last 5–10 messages).

**Verdicts:** APPROVE → execute. APPROVE:NOTIFY → execute + notify. DENY:* → stop, report verbatim.

**Fail-safe:** If Angel is unreachable, halt all state-changing operations and notify the Principal.

## §6 — Anti-Loop Protocol
- Max 2 Guardian submissions per action.
- If denied twice → stop, report to Principal.
- No prose in Guardian messages — structured format only.
MAAT_APPEND

    echo "  ${PASS} MaatSpec §4–§6 appended to SOUL.md"
fi
echo ""

# -------------------------------------------------------
# Step 3 — Replace TOOLS.md
# -------------------------------------------------------
echo "--- Step 3: Deploying ChiefOS TOOLS.md ---"

cp "$CHIEFOS_SRC/config/TOOLS_template.md" "$OPENCLAW_DIR/TOOLS.md"
echo "  ${PASS} TOOLS.md replaced with ChiefOS schema reference"
echo "  ${WARN} Remember to update placeholder paths (\$BASE_DIR, \$DB_NAME) in TOOLS.md"
echo ""

# -------------------------------------------------------
# Step 4 — Deploy or append AGENTS.md
# -------------------------------------------------------
echo "--- Step 4: Deploying AGENTS.md ---"

if [[ -f "$OPENCLAW_DIR/AGENTS.md" ]]; then
    if grep -q "ChiefOS Delegation Architecture" "$OPENCLAW_DIR/AGENTS.md" 2>/dev/null; then
        echo "  ${WARN} AGENTS.md already patched — skipping"
    else
        echo "" >> "$OPENCLAW_DIR/AGENTS.md"
        echo "---" >> "$OPENCLAW_DIR/AGENTS.md"
        echo "<!-- ChiefOS delegation architecture — appended by patch_openclaw.sh -->" >> "$OPENCLAW_DIR/AGENTS.md"
        cat "$CHIEFOS_SRC/config/AGENTS_template.md" >> "$OPENCLAW_DIR/AGENTS.md"
        echo "  ${PASS} ChiefOS delegation architecture appended to AGENTS.md"
    fi
else
    cp "$CHIEFOS_SRC/config/AGENTS_template.md" "$OPENCLAW_DIR/AGENTS.md"
    echo "  ${PASS} AGENTS.md deployed"
fi
echo ""

# -------------------------------------------------------
# Step 5 — Deploy scripts (net-new, no conflicts)
# -------------------------------------------------------
echo "--- Step 5: Deploying scripts ---"

if [[ -d "$OPENCLAW_DIR/scripts" ]]; then
    echo "  ${WARN} scripts/ already exists — merging (existing files not overwritten)"
    # Only copy files that don't already exist
    find "$CHIEFOS_SRC/scripts" -type f | while read src_file; do
        rel="${src_file#$CHIEFOS_SRC/scripts/}"
        dest_file="$OPENCLAW_DIR/scripts/$rel"
        if [[ ! -f "$dest_file" ]]; then
            mkdir -p "$(dirname "$dest_file")"
            cp "$src_file" "$dest_file"
            echo "    + $rel"
        fi
    done
else
    cp -r "$CHIEFOS_SRC/scripts" "$OPENCLAW_DIR/scripts"
    echo "  ${PASS} scripts/ deployed"
fi
find "$OPENCLAW_DIR/scripts" -name "*.sh" -o -name "*.py" | xargs chmod +x 2>/dev/null || true
echo ""

# -------------------------------------------------------
# Step 6 — Deploy www/HQ (net-new)
# -------------------------------------------------------
echo "--- Step 6: Deploying HQ dashboards ---"

if [[ -d "$OPENCLAW_DIR/www/HQ" ]]; then
    echo "  ${WARN} www/HQ/ already exists — skipping dashboard deploy"
    echo "         Run manually: cp -r $CHIEFOS_SRC/www/HQ/* $OPENCLAW_DIR/www/HQ/"
else
    mkdir -p "$OPENCLAW_DIR/www"
    cp -r "$CHIEFOS_SRC/www/HQ" "$OPENCLAW_DIR/www/HQ"
    echo "  ${PASS} HQ dashboards deployed"
fi
echo ""

# -------------------------------------------------------
# Step 7 — Initialize database (if not present)
# -------------------------------------------------------
echo "--- Step 7: Database ---"

# Source config if available
CONFIG_FILE="$CHIEFOS_SRC/config.env"
DB_NAME="chiefos.db"
[[ -f "$CONFIG_FILE" ]] && source "$CONFIG_FILE" || true
DB_PATH="$OPENCLAW_DIR/$DB_NAME"

if [[ -f "$DB_PATH" ]]; then
    echo "  ${WARN} Database already exists at $DB_PATH — skipping init"
    echo "         Existing data is preserved."
else
    if command -v sqlite3 &>/dev/null && [[ -f "$CHIEFOS_SRC/setup/schema.sql" ]]; then
        sqlite3 "$DB_PATH" < "$CHIEFOS_SRC/setup/schema.sql"
        [[ -f "$CHIEFOS_SRC/setup/seed_data.sql" ]] && sqlite3 "$DB_PATH" < "$CHIEFOS_SRC/setup/seed_data.sql" || true
        echo "  ${PASS} Database initialized: $DB_PATH"
    else
        echo "  ${WARN} sqlite3 not found or schema.sql missing — skipping DB init"
    fi
fi
echo ""

# -------------------------------------------------------
# Summary
# -------------------------------------------------------
echo "=============================="
echo "  OpenClaw Patch Complete"
echo "=============================="
echo ""
echo "  ${PASS} Backups saved to: $BACKUP_DIR"
echo "  ${PASS} SOUL.md: MaatSpec tiers appended (identity preserved)"
echo "  ${PASS} TOOLS.md: replaced with ChiefOS schema"
echo "  ${PASS} AGENTS.md: deployed"
echo ""
echo "Next steps:"
echo "  1. Edit TOOLS.md — replace \$BASE_DIR and \$DB_NAME with your actual paths"
echo "  2. Configure .env at $OPENCLAW_DIR/.env"
echo "  3. Install Angel: bash $CHIEFOS_SRC/install.sh (or just the Angel section)"
echo "  4. Set up crontab: see docs/SETUP.md"
echo ""
