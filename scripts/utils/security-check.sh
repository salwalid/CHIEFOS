#!/bin/bash
# security-check.sh — Daily security status check
# Reviews system security posture and alerts on issues

set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
REPORT_FILE="${BASE_DIR}/logs/security-check-latest.txt"
LOG_DIR="${BASE_DIR}/logs"

mkdir -p "$LOG_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" > "$REPORT_FILE"
echo "🔐 SECURITY CHECK REPORT" >> "$REPORT_FILE"
echo "Time: $TIMESTAMP" >> "$REPORT_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

ISSUES=0

# Check 1: fail2ban status
echo "📌 fail2ban Status:" >> "$REPORT_FILE"
if systemctl is-active --quiet fail2ban; then
    echo "  ✅ Active and running" >> "$REPORT_FILE"
else
    echo "  🔴 ISSUE: fail2ban is not running!" >> "$REPORT_FILE"
    ISSUES=$((ISSUES + 1))
fi
echo "" >> "$REPORT_FILE"

# Check 2: UFW firewall status (requires sudo)
echo "📌 UFW Firewall:" >> "$REPORT_FILE"
if [ -x "/usr/sbin/ufw" ]; then
    echo "  ✅ UFW installed" >> "$REPORT_FILE"
    echo "  ⚠️  Status check requires sudo (run manually: sudo ufw status)" >> "$REPORT_FILE"
else
    echo "  ⚠️  UFW not found" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Check 3: SSH root login (check config file)
echo "📌 SSH Root Login:" >> "$REPORT_FILE"
if grep -q "^PermitRootLogin no" /etc/ssh/sshd_config 2>/dev/null; then
    echo "  ✅ Root login disabled" >> "$REPORT_FILE"
else
    echo "  🔴 ISSUE: Root login may be enabled!" >> "$REPORT_FILE"
    ISSUES=$((ISSUES + 1))
fi
echo "" >> "$REPORT_FILE"

# Check 4: Failed SSH attempts (last 24h) - requires sudo
echo "📌 Failed SSH Attempts (24h):" >> "$REPORT_FILE"
echo "  ⚠️  Log analysis requires sudo" >> "$REPORT_FILE"
echo "  Manual check: sudo grep 'Failed password' /var/log/auth.log | tail -20" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Check 5: Pending security updates
echo "📌 Security Updates:" >> "$REPORT_FILE"
UPGRADABLE=$(apt list --upgradable 2>/dev/null | grep -v "Listing" | grep -v "WARNING" | wc -l || true)
if [ "$UPGRADABLE" -eq 0 ]; then
    echo "  ✅ System up to date" >> "$REPORT_FILE"
else
    echo "  ⚠️  $UPGRADABLE packages can be upgraded" >> "$REPORT_FILE"
    apt list --upgradable 2>/dev/null | grep -v "Listing" | grep -v "WARNING" | head -5 >> "$REPORT_FILE" || true
fi
echo "" >> "$REPORT_FILE"

# Check 6: Critical file permissions
echo "📌 Config File Permissions:" >> "$REPORT_FILE"
PERM_ISSUES=0
for file in ~/.config/chiefos/agent.json; do
    if [ -f "$file" ]; then
        PERMS=$(stat -c "%a" "$file")
        if [ "$PERMS" = "600" ]; then
            echo "  ✅ $file: $PERMS" >> "$REPORT_FILE"
        else
            echo "  🔴 $file: $PERMS (should be 600)" >> "$REPORT_FILE"
            PERM_ISSUES=$((PERM_ISSUES + 1))
        fi
    fi
done
if [ $PERM_ISSUES -gt 0 ]; then
    ISSUES=$((ISSUES + PERM_ISSUES))
fi
echo "" >> "$REPORT_FILE"

# Check 7: ChiefOS Gateway status
echo "📌 ChiefOS Gateway:" >> "$REPORT_FILE"
if pgrep -f "${COS_USER:-chiefos}.*gateway" > /dev/null; then
    echo "  ✅ Running" >> "$REPORT_FILE"
    GATEWAY_PID=$(pgrep -f "${COS_USER:-chiefos}.*gateway" | head -1)
    echo "  Process: $GATEWAY_PID" >> "$REPORT_FILE"
else
    echo "  🔴 ISSUE: Gateway not running!" >> "$REPORT_FILE"
    ISSUES=$((ISSUES + 1))
fi
echo "" >> "$REPORT_FILE"

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$REPORT_FILE"
if [ $ISSUES -eq 0 ]; then
    echo "✅ OVERALL STATUS: GOOD" >> "$REPORT_FILE"
else
    echo "⚠️  OVERALL STATUS: $ISSUES ISSUE(S) FOUND" >> "$REPORT_FILE"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$REPORT_FILE"

# Output to stdout
cat "$REPORT_FILE"

# Archive with timestamp
cp "$REPORT_FILE" "$LOG_DIR/security-check-$(date -u +%Y%m%d-%H%M%S).txt"

# Return exit code based on issues
exit $ISSUES
