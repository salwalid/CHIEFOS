#!/bin/bash
# deep-security-report.sh — Comprehensive security report (Tier 2)
# Runs as ROOT via root's crontab
# Frequency: Mon/Wed/Fri at 9am your city time (14:00 UTC)

set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
TIMESTAMP_LOCAL=$(TZ=$TZ date +"%Y-%m-%d %I:%M %p %Z")
LOGS_DIR="${BASE_DIR}/logs"
REPORT_FILE="$LOGS_DIR/deep-security-$(date -u +%Y%m%d-%H%M%S).txt"

mkdir -p "$LOGS_DIR"

# Generate comprehensive report
{
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔐 DEEP SECURITY REPORT"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Generated: $TIMESTAMP_LOCAL"
    echo "UTC: $TIMESTAMP"
    echo ""
    
    # SECTION 1: Core Security Status
    echo "═══════════════════════════════════════════"
    echo "📊 CORE SECURITY STATUS"
    echo "═══════════════════════════════════════════"
    echo ""
    
    # fail2ban
    echo "🛡️  fail2ban:"
    if systemctl is-active --quiet fail2ban; then
        echo "   ✅ Active and protecting SSH"
        BANNED=$(fail2ban-client status sshd 2>/dev/null | grep "Currently banned" | awk '{print $4}' 2>/dev/null || echo "0")
        BANNED=${BANNED:-0}  # Default to 0 if empty
        echo "   Currently banned IPs: $BANNED"
    else
        echo "   🔴 NOT RUNNING!"
    fi
    echo ""
    
    # UFW Firewall
    echo "🔥 UFW Firewall:"
    ufw status verbose | head -15 | sed 's/^/   /'
    echo ""
    
    # SSH Configuration
    echo "🔑 SSH Configuration:"
    if grep -q "^PermitRootLogin no" /etc/ssh/sshd_config; then
        echo "   ✅ Root login disabled"
    else
        echo "   ⚠️  Root login may be enabled"
    fi
    if systemctl is-active --quiet ssh; then
        echo "   ✅ SSH service running"
    else
        echo "   🔴 SSH service not running!"
    fi
    echo ""
    
    # System Updates
    echo "📦 System Updates:"
    UPGRADABLE=$(apt list --upgradable 2>/dev/null | grep -v "Listing" | grep -v "WARNING" | wc -l 2>/dev/null || echo "0")
    # Ensure UPGRADABLE is a valid integer
    if ! [[ "$UPGRADABLE" =~ ^[0-9]+$ ]]; then
        UPGRADABLE=0
    fi
    if [ "$UPGRADABLE" -eq 0 ]; then
        echo "   ✅ System fully updated"
    else
        echo "   ⚠️  $UPGRADABLE packages pending update"
        apt list --upgradable 2>/dev/null | grep -v "Listing" | grep -v "WARNING" | head -5 | sed 's/^/      /' 2>/dev/null || true
    fi
    echo ""
    
    # SECTION 2: Access Analysis
    echo "═══════════════════════════════════════════"
    echo "👤 ACCESS ANALYSIS (Last 7 Days)"
    echo "═══════════════════════════════════════════"
    echo ""
    
    # Recent successful logins
    echo "✅ Successful Logins (Last 10):"
    last -10 -F | head -12 | tail -10 | sed 's/^/   /'
    echo ""
    
    # Failed SSH attempts
    echo "❌ Failed SSH Attempts (Last 7 Days):"
    FAILED_COUNT=$(grep "Failed password" /var/log/auth.log 2>/dev/null | wc -l 2>/dev/null || echo "0")
    # Ensure FAILED_COUNT is a valid integer
    if ! [[ "$FAILED_COUNT" =~ ^[0-9]+$ ]]; then
        FAILED_COUNT=0
    fi
    if [ "$FAILED_COUNT" -eq 0 ]; then
        echo "   ✅ No failed attempts detected"
    else
        echo "   ⚠️  Total failed attempts: $FAILED_COUNT"
        echo ""
        echo "   Top 5 attacking IPs:"
        grep "Failed password" /var/log/auth.log 2>/dev/null | \
            grep -oE "([0-9]{1,3}\.){3}[0-9]{1,3}" | \
            sort | uniq -c | sort -rn | head -5 | \
            awk '{print "      " $1 " attempts from " $2}' 2>/dev/null || true
    fi
    echo ""
    
    # Current SSH sessions
    echo "🔌 Current SSH Sessions:"
    WHO_OUTPUT=$(who)
    if [ -z "$WHO_OUTPUT" ]; then
        echo "   No active sessions"
    else
        echo "$WHO_OUTPUT" | sed 's/^/   /'
    fi
    echo ""
    
    # SECTION 3: System Health
    echo "═══════════════════════════════════════════"
    echo "💻 SYSTEM HEALTH"
    echo "═══════════════════════════════════════════"
    echo ""
    
    # Uptime
    echo "⏱️  Uptime:"
    uptime -p | sed 's/^/   /'
    echo ""
    
    # Disk usage
    echo "💾 Disk Usage:"
    df -h / | tail -1 | awk '{print "   Root: " $3 " used of " $2 " (" $5 " full)"}'
    echo ""
    
    # Memory usage
    echo "🧠 Memory Usage:"
    free -h | grep "Mem:" | awk '{print "   " $3 " used of " $2 " (" int($3/$2*100) "% full)"}'
    echo ""
    
    # Agent Gateway
    echo "🤖 Agent Gateway:"
    if pgrep -f "${COS_USER:-chiefos}.*gateway" > /dev/null; then
        GATEWAY_PID=$(pgrep -f "${COS_USER:-chiefos}.*gateway" | head -1)
        echo "   ✅ Running (PID: $GATEWAY_PID)"
        ps -p "$GATEWAY_PID" -o %cpu,%mem,etime --no-headers | \
            awk '{print "   CPU: " $1 "% | Mem: " $2 "% | Runtime: " $3}'
    else
        echo "   🔴 NOT RUNNING!"
    fi
    echo ""
    
    # SECTION 4: Recent Security Events
    echo "═══════════════════════════════════════════"
    echo "📜 RECENT SECURITY EVENTS (24h)"
    echo "═══════════════════════════════════════════"
    echo ""
    
    # Authentication events
    echo "🔐 Authentication Events:"
    journalctl --since "24 hours ago" -u ssh -u sshd 2>/dev/null | \
        grep -i "accept\|fail\|disconnect\|invalid" | tail -10 | sed 's/^/   /' || \
        echo "   No significant events"
    echo ""
    
    # SECTION 5: Summary
    echo "═══════════════════════════════════════════"
    echo "📋 SUMMARY"
    echo "═══════════════════════════════════════════"
    
    ISSUES=0
    
    # Count issues
    systemctl is-active --quiet fail2ban || ISSUES=$((ISSUES + 1))
    systemctl is-active --quiet ssh || ISSUES=$((ISSUES + 1))
    grep -q "^PermitRootLogin no" /etc/ssh/sshd_config 2>/dev/null || ISSUES=$((ISSUES + 1))
    if [[ "$UPGRADABLE" =~ ^[0-9]+$ ]] && [ "$UPGRADABLE" -gt 0 ]; then
        ISSUES=$((ISSUES + 1))
    fi
    pgrep -f "${COS_USER:-chiefos}.*gateway" > /dev/null || ISSUES=$((ISSUES + 1))
    
    if [ "$ISSUES" -eq 0 ]; then
        echo "✅ Overall Status: EXCELLENT"
        echo "   No security issues detected"
    else
        echo "⚠️  Overall Status: $ISSUES ISSUE(S) DETECTED"
        echo "   Review sections above for details"
    fi
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Next report: $(TZ="${TZ:-UTC}" date -d "next Monday 9:00" '+%A, %B %d at %I:%M %p %Z' 2>/dev/null || echo 'Monday 9:00 AM')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
} > "$REPORT_FILE"

# Send via alert script
bash "${BASE_DIR}/scripts/utils/send_alert.sh" "$REPORT_FILE"

# Archive report
chown "${COS_USER:-chiefos}":"${COS_USER:-chiefos}" "$REPORT_FILE"

# Cleanup old deep reports (keep last 30 days)
find "$LOGS_DIR" -name "deep-security-*.txt" -type f -mtime +30 -delete

echo "Deep security report sent successfully"
