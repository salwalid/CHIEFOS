#!/bin/bash
# add_cron_entries.sh — Add Phase 3 alert script crons + fix existing ones
# Run as: bash $CHIEFOS_HOME/scripts/add_cron_entries.sh

echo "Reading current crontab..."
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M).txt
echo "Backup saved."

# Build new crontab
crontab - << 'CRON'
PATH=$HOME/.local/share/pnpm:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# All times are UTC. Server is UTC, owner is EST (UTC-5). Add 5hrs to get EST equivalent.

# --- EXISTING (unchanged) ---
@reboot nohup python3 $CHIEFOS_HOME/www/HQ/office/update_status.py > $CHIEFOS_HOME/www/HQ/office/updater.log 2>&1 &

# 4:00am EST = 9:00am UTC
0 9 * * * cd $CHIEFOS_HOME && source .env && python3 scripts/daily_briefing_v11.py >> logs/cron.log 2>&1

# --- MASTER HYDRATION ---
# 2:15am EST = 7:15am UTC
15 7 * * * cd $CHIEFOS_HOME && /bin/bash scripts/master_hydration.sh >> logs/master_hydration.log 2>&1

# --- SECURITY ---
# 7am/12pm/8pm EST = 12pm/5pm/1am UTC
0 1,12,17 * * * $CHIEFOS_HOME/scripts/cron-security-monitor.sh >> $CHIEFOS_HOME/logs/cron-execution.log 2>&1
# 4:15pm EST = 9:15pm UTC
15 21 * * * cd $CHIEFOS_HOME && /bin/bash scripts/executive-security-summary.sh >> logs/cron-execution.log 2>&1

# --- CONTENT ---
# 9:45am EST = 2:45pm UTC
45 14 * * 1,3,5 $CHIEFOS_HOME/scripts/remind_post.sh

# --- PHASE 3: ALERT SCRIPTS ---
# 5:00am EST = 10:00am UTC
0 10 * * * cd $CHIEFOS_HOME && python3 scripts/bill_reminder.py >> logs/alerts.log 2>&1
0 10 * * * cd $CHIEFOS_HOME && python3 scripts/deposit_reminder.py >> logs/alerts.log 2>&1
0 10 * * * cd $CHIEFOS_HOME && python3 scripts/maintenance_tracker.py >> logs/alerts.log 2>&1
0 10 * * * cd $CHIEFOS_HOME && python3 scripts/morning_email_review.py >> logs/alerts.log 2>&1

# 5:30am EST = 10:30am UTC
30 10 * * * cd $CHIEFOS_HOME && python3 scripts/todo_alert.py >> logs/alerts.log 2>&1

# 5:45am EST = 10:45am UTC
45 10 * * * cd $CHIEFOS_HOME && python3 scripts/weekly_preview.py >> logs/alerts.log 2>&1

# Sunday 8pm EST = Monday 1:00am UTC
0 1 * * 1 cd $CHIEFOS_HOME && python3 scripts/weekly_preview.py >> logs/alerts.log 2>&1

# Monday 9am EST = Monday 2:00pm UTC
0 14 * * 1 cd $CHIEFOS_HOME && python3 scripts/project_status.py >> logs/alerts.log 2>&1

# Last day of month 9pm EST = 1st of month 2:00am UTC
0 2 1 * * cd $CHIEFOS_HOME && python3 scripts/monthly_summary.py >> logs/alerts.log 2>&1

# --- EMAIL CHECK ---
*/30 * * * * cd $CHIEFOS_HOME && python3 scripts/check_emails.py >> logs/email_check.log 2>&1

CRON

echo "✅ Crontab updated. New entries:"
crontab -l
