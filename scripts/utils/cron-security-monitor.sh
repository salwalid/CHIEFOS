#!/bin/bash
# cron-security-monitor.sh — Hourly security monitoring with Telegram alerts
# Run via cron every hour

set -euo pipefail

SCRIPTS_DIR="${BASE_DIR}/scripts"
LOGS_DIR="${BASE_DIR}/logs"
REPORT_FILE="$LOGS_DIR/cron-report-$(date -u +%Y%m%d-%H%M%S).txt"

# Initialize report
{
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔐 HOURLY SECURITY MONITOR"
    echo "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
} > "$REPORT_FILE"

ALERT_NEEDED=false
ISSUES_FOUND=0

# Run security check
echo "Running security check..." >> "$REPORT_FILE"
if "$SCRIPTS_DIR/security-check.sh" >> "$REPORT_FILE" 2>&1; then
    echo "✅ Security check passed" >> "$REPORT_FILE"
else
    ISSUES_FOUND=$?
    echo "⚠️  Security check found $ISSUES_FOUND issue(s)" >> "$REPORT_FILE"
    ALERT_NEEDED=true
fi

echo "" >> "$REPORT_FILE"

# Determine if we should send notification
CURRENT_HOUR=$(date +%H)

# Send alert if:
# 1. Issues found, OR
# 2. Top of every 6 hours for status update (00:00, 06:00, 12:00, 18:00)
if [ "$ALERT_NEEDED" = true ]; then
    NOTIFICATION_TYPE="ALERT"
elif [ $((10#$CURRENT_HOUR % 6)) -eq 0 ]; then
    NOTIFICATION_TYPE="STATUS"
else
    NOTIFICATION_TYPE="NONE"
fi

if [ "$NOTIFICATION_TYPE" != "NONE" ]; then
    # Create notification
    NOTIF_FILE="$LOGS_DIR/notification-pending.txt"
    
    if [ "$NOTIFICATION_TYPE" = "ALERT" ]; then
        {
            echo "🚨 SECURITY ALERT"
            echo ""
            echo "Issues detected during hourly security check:"
            echo ""
            tail -n 30 "$LOGS_DIR/security-check-latest.txt"
            echo ""
            echo "Full report: $REPORT_FILE"
        } > "$NOTIF_FILE"
    else
        {
            echo "✅ Security Status (Scheduled Check)"
            echo ""
            tail -n 15 "$LOGS_DIR/security-check-latest.txt"
            echo ""
            echo "Next update in 6 hours unless issues detected."
        } > "$NOTIF_FILE"
    fi
    
    # Send via ChiefOS message tool
    # Note: This requires ChiefOS gateway to be running
    "$SCRIPTS_DIR/send_alert.sh" "$NOTIF_FILE" 2>&1 >> "$REPORT_FILE" || {
        echo "⚠️  Failed to send Telegram notification" >> "$REPORT_FILE"
    }
    
    # Archive notification
    cp "$NOTIF_FILE" "$LOGS_DIR/notification-sent-$(date -u +%Y%m%d-%H%M%S).txt"
    rm "$NOTIF_FILE"
fi

# Cleanup old reports (keep last 168 = 1 week)
find "$LOGS_DIR" -name "cron-report-*.txt" -type f | sort | head -n -168 | xargs -r rm

echo "Monitoring complete." >> "$REPORT_FILE"
exit 0
