#!/bin/bash
# executive-security-summary.sh — 4:00 AM Daily Security Report
# Consolidates all security pillars into a decision-ready summary for the Principal

set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
REPORT_FILE="${BASE_DIR}/logs/executive-security-$(date -u +%Y%m%d).txt"

# 1. RUN COMPONENT SCRIPTS
${BASE_DIR}/scripts/security-check.sh > /dev/null || true
${BASE_DIR}/scripts/activity-summary.sh > /dev/null || true

# 2. COMPILE SUMMARY
{
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🛡️ CHIEFOS EXECUTIVE SECURITY SUMMARY"
    echo "📅 $(date +"%A, %B %d, %Y")"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # PILLAR 1: Infrastructure
    echo "🏗️ PILLAR 1: INFRASTRUCTURE"
    if systemctl is-active --quiet fail2ban; then
        echo "  ✅ Fail2Ban: ACTIVE"
    else
        echo "  🔴 Fail2Ban: INACTIVE"
    fi

    # Check for exposed 8080 (since we saw it in manual sweep)
    if ss -tln | grep -q "0.0.0.0:8080"; then
        echo "  ⚠️  Port 8080: Bound to 0.0.0.0 (Ensure UFW is blocking external traffic)"
    else
        echo "  ✅ Port 8080: Localhost only"
    fi
    echo ""

    # PILLAR 2: Access & Identity
    echo "👤 PILLAR 2: ACCESS & IDENTITY"
    FAILED_LOGINS=$(grep -c "Failed password" /var/log/auth.log 2>/dev/null || echo "0")
    if [ "$FAILED_LOGINS" -eq 0 ]; then
        echo "  ✅ Brute Force: No failed attempts detected."
    else
        echo "  ⚠️  Brute Force: $FAILED_LOGINS failed login attempts (Check logs)."
    fi
    
    ACTIVE_SESSIONS=$(who | wc -l)
    echo "  🔌 Active SSH Sessions: $ACTIVE_SESSIONS"
    echo ""

    # PILLAR 3: System Health
    echo "📦 PILLAR 3: SYSTEM HEALTH"
    UPGRADABLE=$(apt list --upgradable 2>/dev/null | grep -v "Listing" | wc -l || echo "0")
    if [ "$UPGRADABLE" -le 1 ]; then
        echo "  ✅ Updates: System up to date."
    else
        echo "  ⚠️  Updates: $UPGRADABLE security patches pending."
    fi
    echo ""

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 VERDICT: $( [ "$FAILED_LOGINS" -eq 0 ] && echo "PERIMETER SECURE" || echo "NEEDS REVIEW" )"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Full logs available at: ${BASE_DIR}/logs/"

} > "$REPORT_FILE"

# 3. DELIVER TO USER
bash "${BASE_DIR}/scripts/utils/send_alert.sh" "$REPORT_FILE"

echo "Executive summary delivered."
