#!/bin/bash
# ChiefOS Security Data Feed - Daily Timestamped
# Captures external attack data and system security events

(
  echo "--- UFW STATUS ---"
  sudo ufw status
  
  echo -e "\n--- FAILED LOGINS ---"
  # Capture real failed attempts from auth.log
  sudo grep "Failed password" /var/log/auth.log | tail -n 100
  
  echo -e "\n--- FAIL2BAN BANS ---"
  # Capture real bans from fail2ban.log
  sudo grep "Ban " /var/log/fail2ban.log | tail -n 100
  
  echo -e "\n--- AGENT DEEP AUDIT ---"
  echo "Deep audit: configure AGENT_CLI in config.env to enable agent-driven audit"
) > ${BASE_DIR}/logs/security_$(date +%Y-%m-%d).log 2>&1

# Ensure ChiefOS user can read the log
chown "${COS_USER:-chiefos}":"${COS_USER:-chiefos}" ${BASE_DIR}/logs/security_$(date +%Y-%m-%d).log
