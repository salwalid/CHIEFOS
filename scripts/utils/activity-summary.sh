#!/bin/bash
# activity-summary.sh — Daily activity summary
# Summarizes system activity over the last 24 hours

set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
REPORT_FILE="${BASE_DIR}/logs/activity-summary-latest.txt"
LOG_DIR="${BASE_DIR}/logs"

mkdir -p "$LOG_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" > "$REPORT_FILE"
echo "📊 ACTIVITY SUMMARY (24h)" >> "$REPORT_FILE"
echo "Time: $TIMESTAMP" >> "$REPORT_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Recent logins (last 10)
echo "📌 Recent Logins:" >> "$REPORT_FILE"
echo "  ⚠️  Requires sudo: sudo last -10" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Current SSH sessions
echo "📌 Current SSH Sessions:" >> "$REPORT_FILE"
SSH_COUNT=$(who | wc -l)
if [ "$SSH_COUNT" -eq 0 ]; then
    echo "  No active SSH sessions" >> "$REPORT_FILE"
else
    echo "  $SSH_COUNT active session(s):" >> "$REPORT_FILE"
    who | awk '{print "    - " $1 " from " $5 " at " $3 " " $4}' >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# System uptime
echo "📌 System Uptime:" >> "$REPORT_FILE"
uptime -p >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Disk usage
echo "📌 Disk Usage:" >> "$REPORT_FILE"
df -h / | tail -1 | awk '{print "  Root: " $3 " used of " $2 " (" $5 " full)"}' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Memory usage
echo "📌 Memory Usage:" >> "$REPORT_FILE"
free -h | grep "Mem:" | awk '{print "  " $3 " used of " $2}' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Agent gateway process info
echo "📌 Agent Gateway:" >> "$REPORT_FILE"
if pgrep -f "${COS_USER:-chiefos}.*gateway" > /dev/null; then
    GATEWAY_PID=$(pgrep -f "${COS_USER:-chiefos}.*gateway" | head -1)
    echo "  PID: $GATEWAY_PID" >> "$REPORT_FILE"
    ps -p "$GATEWAY_PID" -o %cpu,%mem,etime,cmd --no-headers | awk '{print "  CPU: " $1 "% | Mem: " $2 "% | Runtime: " $3}' >> "$REPORT_FILE"
else
    echo "  ⚠️  Gateway not running" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$REPORT_FILE"

# Output to stdout
cat "$REPORT_FILE"

# Archive with timestamp
cp "$REPORT_FILE" "$LOG_DIR/activity-summary-$(date -u +%Y%m%d-%H%M%S).txt"
