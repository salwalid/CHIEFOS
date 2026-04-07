#!/usr/bin/env bash
# =============================================================
# ChiefOS Installation Verifier
# Run this at any time to check system health.
# Usage: bash verify-install.sh
# =============================================================

set -euo pipefail

PASS="✅"
WARN="⚠️ "
FAIL="❌"
ISSUES=0
WARNINGS=0

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║      ChiefOS Installation Verifier       ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Load config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.env"

if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
elif [[ -f "$HOME/chiefos/.env" ]]; then
    source "$HOME/chiefos/.env"
else
    echo "${FAIL} config.env not found. Run from the CHIEFOS directory."
    exit 1
fi

DB_PATH="${BASE_DIR}/${DB_NAME}"
ANGEL_PORT="${ANGEL_PORT:-39571}"

# -------------------------------------------------------
# 1. Web UI
# -------------------------------------------------------
echo "--- Web UI ---"
if curl -sf --max-time 5 "http://127.0.0.1/HQ/" > /dev/null 2>&1; then
    echo "${PASS} Web UI reachable at http://$BASE_URL/HQ/"
else
    echo "${WARN} Web UI not reachable locally"
    echo "     Check: sudo systemctl status nginx"
    echo "     Fix:   sudo systemctl reload nginx"
    WARNINGS=$((WARNINGS + 1))
fi

# -------------------------------------------------------
# 2. Angel MCP endpoint
# -------------------------------------------------------
echo ""
echo "--- Angel Governance ---"
if curl -sf --max-time 5 "http://127.0.0.1:$ANGEL_PORT/mcp" > /dev/null 2>&1; then
    echo "${PASS} Angel MCP endpoint responding at http://127.0.0.1:$ANGEL_PORT/mcp"
else
    echo "${WARN} Angel MCP endpoint not responding"
    echo "     Check: sudo -u angel pm2 list"
    echo "     Fix:   sudo -u angel pm2 restart angel"
    WARNINGS=$((WARNINGS + 1))
fi

# Check PM2 process
if sudo -u angel pm2 list 2>/dev/null | grep -q "angel.*online"; then
    echo "${PASS} Angel PM2 process: online"
else
    echo "${WARN} Angel PM2 process not listed as online"
    WARNINGS=$((WARNINGS + 1))
fi

# -------------------------------------------------------
# 3. Database
# -------------------------------------------------------
echo ""
echo "--- Database ---"
if [[ -f "$DB_PATH" ]]; then
    TABLE_COUNT=$(sqlite3 "$DB_PATH" "SELECT count(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo 0)
    ROW_COUNT=$(sqlite3 "$DB_PATH" "SELECT count(*) FROM table_Todos;" 2>/dev/null || echo 0)
    if [[ "$TABLE_COUNT" -ge 25 ]]; then
        echo "${PASS} Database: $TABLE_COUNT tables, $ROW_COUNT todos"
    else
        echo "${FAIL} Database has only $TABLE_COUNT tables (expected 25+)"
        echo "     Fix: bash $SCRIPT_DIR/setup/verify_db.sh $DB_PATH"
        ISSUES=$((ISSUES + 1))
    fi
else
    echo "${FAIL} Database not found at $DB_PATH"
    echo "     Fix: sudo -u $COS_USER sqlite3 $DB_PATH < $SCRIPT_DIR/setup/schema.sql"
    ISSUES=$((ISSUES + 1))
fi

# -------------------------------------------------------
# 4. Scripts
# -------------------------------------------------------
echo ""
echo "--- Scripts ---"
SCRIPT_COUNT=$(find "$BASE_DIR/scripts" -name "*.py" -o -name "*.sh" 2>/dev/null | wc -l || echo 0)
if [[ "$SCRIPT_COUNT" -ge 30 ]]; then
    echo "${PASS} Scripts: $SCRIPT_COUNT deployed"
else
    echo "${FAIL} Only $SCRIPT_COUNT scripts found — expected 30+"
    ISSUES=$((ISSUES + 1))
fi

KEY_SCRIPTS=(
    "$BASE_DIR/scripts/core/add_todo.py"
    "$BASE_DIR/scripts/core/master_hydration.sh"
    "$BASE_DIR/scripts/utils/send_alert.sh"
    "$BASE_DIR/scripts/utils/load_env.sh"
)
for s in "${KEY_SCRIPTS[@]}"; do
    if [[ -f "$s" ]]; then
        echo "${PASS} $(basename $s) present"
    else
        echo "${FAIL} Missing: $s"
        ISSUES=$((ISSUES + 1))
    fi
done

# -------------------------------------------------------
# 5. Crontab
# -------------------------------------------------------
echo ""
echo "--- Crontab ---"
CRON_COUNT=$(sudo crontab -u "$COS_USER" -l 2>/dev/null | grep -v "^#" | grep -v "^$" | wc -l || echo 0)
if [[ "$CRON_COUNT" -ge 10 ]]; then
    echo "${PASS} Crontab: $CRON_COUNT jobs scheduled for $COS_USER"
else
    echo "${WARN} Only $CRON_COUNT cron jobs found (expected 10+)"
    echo "     Check: sudo crontab -u $COS_USER -l"
    WARNINGS=$((WARNINGS + 1))
fi

if sudo systemctl is-active --quiet cron 2>/dev/null || sudo systemctl is-active --quiet crond 2>/dev/null; then
    echo "${PASS} Cron daemon running"
else
    echo "${FAIL} Cron daemon not running"
    echo "     Fix: sudo systemctl start cron"
    ISSUES=$((ISSUES + 1))
fi

# -------------------------------------------------------
# 6. Dashboards
# -------------------------------------------------------
echo ""
echo "--- Dashboards ---"
PAGE_COUNT=$(find "$BASE_DIR/www/HQ" -name "index.html" 2>/dev/null | wc -l || echo 0)
JSON_COUNT=$(find "$BASE_DIR/www/HQ" -name "*.json" 2>/dev/null | wc -l || echo 0)
if [[ "$PAGE_COUNT" -ge 7 ]]; then
    echo "${PASS} Dashboard pages: $PAGE_COUNT"
else
    echo "${WARN} Only $PAGE_COUNT dashboard pages found"
    WARNINGS=$((WARNINGS + 1))
fi
if [[ "$JSON_COUNT" -ge 3 ]]; then
    echo "${PASS} Dashboard data files: $JSON_COUNT JSON files"
else
    echo "${WARN} Few dashboard data files ($JSON_COUNT) — dashboards may show empty"
    echo "     Fix: sudo -u $COS_USER bash $BASE_DIR/scripts/core/master_hydration.sh"
    WARNINGS=$((WARNINGS + 1))
fi

# -------------------------------------------------------
# 7. Wiki knowledge base
# -------------------------------------------------------
echo ""
echo "--- Wiki Knowledge Base ---"
if [[ -d "$BASE_DIR/wiki" ]]; then
    WIKI_PAGES=$(find "$BASE_DIR/wiki" -name "*.md" 2>/dev/null | wc -l)
    echo "${PASS} Wiki directory present ($WIKI_PAGES markdown files)"
else
    echo "${WARN} Wiki directory missing — run: bash wiki-install.sh"
    WARNINGS=$((WARNINGS + 1))
fi
if [[ -d "$BASE_DIR/raw" ]]; then
    echo "${PASS} Raw source directory present"
else
    echo "${WARN} Raw directory missing"
    WARNINGS=$((WARNINGS + 1))
fi
if [[ -f "$BASE_DIR/wiki/index.md" ]]; then
    echo "${PASS} wiki/index.md present"
else
    echo "${WARN} wiki/index.md missing"
    WARNINGS=$((WARNINGS + 1))
fi

# -------------------------------------------------------
# 8. Governance files
# -------------------------------------------------------
echo ""
echo "--- Governance Files ---"
for f in SOUL.md TOOLS.md AGENTS.md; do
    if [[ -f "$BASE_DIR/$f" ]]; then
        echo "${PASS} $f present"
    else
        echo "${WARN} $f missing at $BASE_DIR/$f"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# -------------------------------------------------------
# 8. Telegram alert test (optional)
# -------------------------------------------------------
echo ""
echo "--- Alert System ---"
if [[ -f "$BASE_DIR/scripts/utils/send_alert.sh" ]] && [[ -n "${TELEGRAM_TOKEN:-}" ]]; then
    echo "${PASS} send_alert.sh present and TELEGRAM_TOKEN configured"
else
    echo "${WARN} Alert system may not be configured — check TELEGRAM_TOKEN in $BASE_DIR/.env"
    WARNINGS=$((WARNINGS + 1))
fi

# -------------------------------------------------------
# SUMMARY
# -------------------------------------------------------
echo ""
echo "=============================="
echo "  Health Check Summary"
echo "=============================="
if [[ "$ISSUES" -eq 0 && "$WARNINGS" -eq 0 ]]; then
    echo "${PASS} All checks passed — ChiefOS is fully operational"
elif [[ "$ISSUES" -eq 0 ]]; then
    echo "${WARN} $WARNINGS warning(s) found — system is running but some features may be degraded"
else
    echo "${FAIL} $ISSUES critical issue(s) and $WARNINGS warning(s) found"
    echo "     Fix the ${FAIL} items above before using ChiefOS"
fi
echo ""
echo "  HQ Dashboard: http://$BASE_URL/HQ/"
echo "  Logs:         $BASE_DIR/logs/"
echo ""
