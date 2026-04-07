#!/bin/bash

# Fetch the last 10 logins
LOGINS=$(last -n 10 | grep -v "wtmp" | grep -v "reboot" | head -n 10)

echo "### 🔐 RECENT LOGIN REPORT (ISP ENRICHED)"
echo "| USER | TTY | IP | ISP / OWNERSHIP | DATE/TIME |"
echo "| :--- | :--- | :--- | :--- | :--- |"

while read -r line; do
    USER=$(echo "$line" | awk '{print $1}')
    TTY=$(echo "$line" | awk '{print $2}')
    IP=$(echo "$line" | awk '{print $3}')
    # Extract date/time (fields 4-7)
    DT=$(echo "$line" | awk '{print $4" "$5" "$6" "$7}')
    
    # Check if IP is actually an IP address
    if [[ $IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        ISP=$(curl -s "http://ip-api.com/json/$IP" | jq -r '.isp // "Unknown"')
    else
        ISP="N/A"
    fi
    
    echo "| $USER | $TTY | $IP | **$ISP** | $DT |"
done <<< "$LOGINS"
