#!/bin/bash
# meta-check.sh — Check the checkers
# Verifies that monitoring infrastructure is in place and functioning

set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
REPORT_FILE="${BASE_DIR}/logs/meta-check-latest.txt"
LOG_DIR="${BASE_DIR}/logs"
SCRIPTS_DIR="${BASE_DIR}/scripts"

mkdir -p "$LOG_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" > "$REPORT_FILE"
echo "🔍 META-CHECK: Monitoring Infrastructure" >> "$REPORT_FILE"
echo "Time: $TIMESTAMP" >> "$REPORT_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

ISSUES=0

# Check 1: Required scripts exist and are executable
echo "📌 Security Scripts:" >> "$REPORT_FILE"
for script in security-check.sh activity-summary.sh meta-check.sh; do
    SCRIPT_PATH="$SCRIPTS_DIR/$script"
    if [ -f "$SCRIPT_PATH" ]; then
        if [ -x "$SCRIPT_PATH" ]; then
            echo "  ✅ $script (executable)" >> "$REPORT_FILE"
        else
            echo "  ⚠️  $script (exists but not executable)" >> "$REPORT_FILE"
            ISSUES=$((ISSUES + 1))
        fi
    else
        echo "  🔴 $script (missing!)" >> "$REPORT_FILE"
        ISSUES=$((ISSUES + 1))
    fi
done
echo "" >> "$REPORT_FILE"

# Check 2: Log directory exists and is writable
echo "📌 Log Directory:" >> "$REPORT_FILE"
if [ -d "$LOG_DIR" ]; then
    if [ -w "$LOG_DIR" ]; then
        echo "  ✅ $LOG_DIR (writable)" >> "$REPORT_FILE"
    else
        echo "  🔴 $LOG_DIR (not writable!)" >> "$REPORT_FILE"
        ISSUES=$((ISSUES + 1))
    fi
else
    echo "  🔴 $LOG_DIR (does not exist!)" >> "$REPORT_FILE"
    ISSUES=$((ISSUES + 1))
fi
echo "" >> "$REPORT_FILE"

# Check 3: Recent check execution
echo "📌 Recent Check Runs:" >> "$REPORT_FILE"
for check in security-check activity-summary; do
    LATEST_LOG="$LOG_DIR/${check}-latest.txt"
    if [ -f "$LATEST_LOG" ]; then
        AGE_SECONDS=$(( $(date +%s) - $(stat -c %Y "$LATEST_LOG") ))
        AGE_HOURS=$(( AGE_SECONDS / 3600 ))
        if [ $AGE_HOURS -lt 25 ]; then
            echo "  ✅ $check: ${AGE_HOURS}h ago" >> "$REPORT_FILE"
        else
            echo "  ⚠️  $check: ${AGE_HOURS}h ago (stale)" >> "$REPORT_FILE"
            ISSUES=$((ISSUES + 1))
        fi
    else
        echo "  ⚠️  $check: never run" >> "$REPORT_FILE"
    fi
done
echo "" >> "$REPORT_FILE"

# Check 4: Cron jobs (if using cron)
echo "📌 Cron Jobs:" >> "$REPORT_FILE"
CRON_JOBS=$(crontab -l 2>/dev/null | grep -v "^#" | grep -c "security-check\|activity-summary" || true)
if [ "$CRON_JOBS" -gt 0 ]; then
    echo "  ✅ $CRON_JOBS monitoring job(s) scheduled" >> "$REPORT_FILE"
else
    echo "  ⚠️  No monitoring cron jobs found — run install.sh to configure crontab" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Check 5: .gitignore exists
echo "📌 Workspace Hygiene:" >> "$REPORT_FILE"
if [ -f "${BASE_DIR}/.gitignore" ]; then
    echo "  ✅ .gitignore present" >> "$REPORT_FILE"
else
    echo "  ⚠️  .gitignore missing" >> "$REPORT_FILE"
    ISSUES=$((ISSUES + 1))
fi
echo "" >> "$REPORT_FILE"

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$REPORT_FILE"
if [ $ISSUES -eq 0 ]; then
    echo "✅ MONITORING INFRASTRUCTURE: HEALTHY" >> "$REPORT_FILE"
else
    echo "⚠️  MONITORING INFRASTRUCTURE: $ISSUES ISSUE(S)" >> "$REPORT_FILE"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$REPORT_FILE"

# Output to stdout
cat "$REPORT_FILE"

# Archive with timestamp
cp "$REPORT_FILE" "$LOG_DIR/meta-check-$(date -u +%Y%m%d-%H%M%S).txt"

exit $ISSUES
