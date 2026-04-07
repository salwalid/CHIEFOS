#!/bin/bash
# Alpha Security Data Feed - Daily Timestamped
# Corrected version to capture real external attack data

(
  echo "--- UFW STATUS ---"
  sudo ufw status
  
  echo -e "\n--- FAILED LOGINS ---"
  # Capture real failed attempts from auth.log
  sudo grep "Failed password" /var/log/auth.log | tail -n 100
  
  echo -e "\n--- FAIL2BAN BANS ---"
  # Capture real bans from fail2ban.log
  sudo grep "Ban " /var/log/fail2ban.log | tail -n 100
  
  echo -e "\n--- CHIEFOS DEEP AUDIT ---"
  command -v chiefos && chiefos security audit --deep || echo "chiefos not installed — skipping deep audit"
) > ${BASE_DIR}/logs/security_$(date +%Y-%m-%d).log 2>&1

# Ensure Alpha can read the log
chown "${COS_USER:-chiefos}":"${COS_USER:-chiefos}" ${BASE_DIR}/logs/security_$(date +%Y-%m-%d).log
