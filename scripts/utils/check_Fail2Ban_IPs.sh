#!/bin/bash

# Alpha Security Auditor v1.1
# Checks top attackers and cross-references with Fail2Ban jails

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛡️  CHIEFOS SECURITY AUDIT: WEB & SSH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. ANALYZE WEB TRAFFIC (NGINX)
echo -e "\n🌐 TOP WEB PROBES (Last 24-48h):"
echo "------------------------------------------------"
TOP_WEB_IPS=$(sudo awk '{print $1}' /var/log/nginx/access.log 2>/dev/null | sort | uniq -c | sort -nr | head -n 5)

if [ -z "$TOP_WEB_IPS" ]; then
    echo "No web traffic found in logs or log file inaccessible."
else
    echo "$TOP_WEB_IPS" | while read count ip; do
        # Get Org Data
        ORG=$(curl -s https://ipapi.co/$ip/yaml | grep "org:" | cut -d':' -f2 | xargs)
        
        # Check Fail2Ban status for this IP
        JAILS=$(sudo fail2ban-client status | grep "Jail list" | sed 's/.*://; s/,//g' | tr ',' ' ')
        BANNED_IN=""
        for jail in $JAILS; do
            if sudo fail2ban-client status "$jail" | grep -Fq "$ip"; then
                BANNED_IN="$jail"
                break
            fi
        done
        
        STATUS="✅ CLEAN"
        [ ! -z "$BANNED_IN" ] && STATUS="🚫 BANNED ($BANNED_IN)"
        
        echo -e "IP: $ip | Hits: $count | Org: ${ORG:-Unknown}"
        echo -e "Status: $STATUS"
        echo "------------------------------------------------"
    done
fi

# 2. ANALYZE SSH BRUTE FORCE
echo -e "\n🔑 SSH BRUTE FORCE ATTEMPTS:"
echo "------------------------------------------------"
TOP_SSH_IPS=$(sudo grep "Failed password" /var/log/auth.log 2>/dev/null | awk '{print $(NF-3)}' | sort | uniq -c | sort -nr | head -n 5)

if [ -z "$TOP_SSH_IPS" ]; then
    echo "No failed SSH attempts found or log file inaccessible."
else
    echo "$TOP_SSH_IPS" | while read count ip; do
        ORG=$(curl -s https://ipapi.co/$ip/yaml | grep "org:" | cut -d':' -f2 | xargs)
        
        # Check Fail2Ban
        BANNED_SSH=$(sudo fail2ban-client status sshd 2>/dev/null | grep -Fq "$ip" && echo "YES" || echo "NO")
        
        STATUS="⚠️  ACTIVE"
        [ "$BANNED_SSH" == "YES" ] && STATUS="🚫 BANNED"
        
        echo -e "IP: $ip | Attempts: $count | Org: ${ORG:-Unknown}"
        echo -e "Status: $STATUS"
        echo "------------------------------------------------"
    done
fi

echo -e "\n✅ Audit Complete."
