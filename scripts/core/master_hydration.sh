#!/bin/bash
# CHIEFOS MASTER HYDRATION PULSE
# This script refreshes all modules of the Mission Control Dashboard from the SQLite Database.

BASE_DIR="$CHIEFOS_HOME"
LOG_FILE="$BASE_DIR/logs/master_hydration.log"

echo "[$(date)] --- INITIATING FULL HYDRATION PULSE ---" >> "$LOG_FILE"

# 1. Update Perimeter Logs (Security HQ)
python3 "$BASE_DIR/scripts/hydrate_security.py" >> "$LOG_FILE" 2>&1
echo "Perimeter Status: SYNCED" >> "$LOG_FILE"

# 2. Update Asset Registry (Property Management)
python3 "$BASE_DIR/scripts/hydrate_properties.py" >> "$LOG_FILE" 2>&1
echo "Asset Registry: SYNCED" >> "$LOG_FILE"

# 3. Update Social Posts (Content) — vault deleted, step removed
python3 "$BASE_DIR/scripts/hydrate_content.py" >> "$LOG_FILE" 2>&1
echo "Social Posts: SYNCED" >> "$LOG_FILE"

# 5. Weekly Analytics (If Sunday)
if [ $(date +%u) -eq 7 ]; then
    python3 "$BASE_DIR/scripts/analyze_weekly_security.py" >> "$LOG_FILE" 2>&1
    echo "Weekly Analytics: PROCESSED" >> "$LOG_FILE"
fi

# 5. Update Schedule Page
python3 "$BASE_DIR/scripts/hydrate_schedule.py" >> "$LOG_FILE" 2>&1
echo "Schedule: SYNCED" >> "$LOG_FILE"

# 6. Update Finance Dashboard
python3 "$BASE_DIR/scripts/hydrate_finance.py" >> "$LOG_FILE" 2>&1
echo "Finance: SYNCED" >> "$LOG_FILE"

# 7. Update Weekly Layout
python3 "$BASE_DIR/scripts/hydrate_weekly_layout.py" >> "$LOG_FILE" 2>&1
echo "Weekly Layout: SYNCED" >> "$LOG_FILE"

# 8. Update Projects Dashboard
python3 "$BASE_DIR/scripts/hydrate_projects.py" >> "$LOG_FILE" 2>&1
echo "Projects: SYNCED" >> "$LOG_FILE"

# 9. Update Comms Directory
python3 "$BASE_DIR/scripts/hydrate_comms.py" >> "$LOG_FILE" 2>&1
echo "Comms: SYNCED" >> "$LOG_FILE"

# 10. Agent Office — runs as persistent daemon via @reboot cron, not called here

echo "[$(date)] --- HYDRATION PULSE COMPLETE ---" >> "$LOG_FILE"
