#!/usr/bin/env bash
# =============================================================
# ChiefOS Installer v1.0
# A self-hosted AI Chief of Staff backend.
#
# Usage: bash install.sh
#
# This script will:
#   1. Run preflight checks
#   2. Read your configuration
#   3. Create system user and directory structure
#   4. Deploy and configure all scripts
#   5. Initialize the database
#   6. Deploy HQ dashboards
#   7. Deploy governance files (SOUL, TOOLS, AGENTS)
#   8. Install Angel (governance service)
#   9. Install crontab
#  10. Run first hydration
# =============================================================

set -euo pipefail

CHIEFOS_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PASS="✅"
WARN="⚠️ "
FAIL="❌"
STEP=0

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
step() {
    STEP=$((STEP + 1))
    echo ""
    echo "════════════════════════════════════════"
    echo "  [STEP $STEP] $1"
    echo "════════════════════════════════════════"
}

ok()   { echo "  ${PASS} $1"; }
warn() { echo "  ${WARN} $1"; }
fail() { echo "  ${FAIL} $1"; exit 1; }

verify() {
    # verify <description> <test_command>
    local desc="$1"
    shift
    if eval "$@" &>/dev/null; then
        ok "$desc"
    else
        fail "$desc — FAILED. Fix and re-run install.sh"
    fi
}

ask() {
    # ask <var_name> <prompt> [default]
    local var="$1"
    local prompt="$2"
    local default="${3:-}"
    if [[ -n "$default" ]]; then
        read -rp "  → $prompt [$default]: " val
        val="${val:-$default}"
    else
        read -rp "  → $prompt: " val
        while [[ -z "$val" ]]; do
            read -rp "  → $prompt (required): " val
        done
    fi
    eval "$var='$val'"
}

# -------------------------------------------------------
# PREFLIGHT
# -------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║         ChiefOS Installer v1.0           ║"
echo "║  A self-hosted AI Chief of Staff backend ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Running preflight checks..."
echo ""

bash "$CHIEFOS_SRC/preflight.sh" || {
    echo ""
    echo "${FAIL} Preflight failed. Fix the issues above and re-run install.sh"
    exit 1
}

# -------------------------------------------------------
# STEP 1 — Configuration
# -------------------------------------------------------
step "Configuration"

CONFIG_FILE="$CHIEFOS_SRC/config.env"

if [[ -f "$CONFIG_FILE" ]]; then
    ok "Loading config from $CONFIG_FILE"
    source "$CONFIG_FILE"
else
    warn "config.env not found — entering interactive setup"
    echo ""
    echo "  You'll need the following before continuing:"
    echo "    - A domain or IP pointing to this server"
    echo "    - A Gmail address + App Password (for email monitoring)"
    echo "    - A Telegram Bot Token + Chat ID (for alerts)"
    echo "    - Angel's GitHub repo URL"
    echo ""

    ask BASE_DIR    "ChiefOS workspace path" "/home/chiefos/chiefos"
    ask COS_USER    "OS username for ChiefOS" "chiefos"

    # Detect public IP before asking for domain so we can show the DNS record to create
    echo ""
    PUBLIC_IP=$(curl -sf --max-time 5 https://api.ipify.org 2>/dev/null || \
                curl -sf --max-time 5 https://ifconfig.me 2>/dev/null || \
                hostname -I | awk '{print $1}')
    echo "  This server's public IP: ${PUBLIC_IP}"
    echo ""
    echo "  Tip: create a subdomain at your domain registrar before entering it here."
    echo "  Example DNS record:"
    echo ""
    echo "    Type:  A"
    echo "    Name:  hq          (the subdomain — e.g. hq.yourdomain.com)"
    echo "    Value: $PUBLIC_IP"
    echo "    TTL:   300"
    echo ""
    echo "  Enter the full subdomain below (e.g. hq.yourdomain.com)."
    echo "  Or enter the IP directly ($PUBLIC_IP) to skip DNS and SSL."
    echo ""
    ask BASE_URL    "Your domain or IP (no http://, no trailing slash)" "$PUBLIC_IP"

    # If a real domain was entered, pause and confirm DNS is set up
    if echo "$BASE_URL" | grep -qP '^[a-zA-Z]'; then
        echo ""
        echo "  ┌──────────────────────────────────────────────────────┐"
        echo "  │  Create this DNS record at your domain registrar:    │"
        echo "  │                                                      │"
        echo "  │    Type:  A                                          │"
        printf  "  │    Name:  %-42s│\n" "$BASE_URL"
        printf  "  │    Value: %-42s│\n" "$PUBLIC_IP"
        echo "  │    TTL:   300 (or lowest available)                  │"
        echo "  └──────────────────────────────────────────────────────┘"
        echo ""
        echo "  DNS propagation usually takes 1–5 minutes."
        echo "  SSL (Certbot) will run at the end of this install — your domain"
        echo "  must be resolving by then for SSL to work."
        echo ""
        read -rp "  → Press Enter once your DNS record is saved, to continue: "
        echo ""
    else
        warn "Using IP address — no DNS record needed. SSL will be skipped (domain required for SSL)."
        echo ""
    fi

    ask DB_NAME     "Database filename" "chiefos.db"
    ask TZ          "Your timezone" "America/New_York"
    ask GMAIL_USER  "Gmail address for email monitoring" ""
    ask GMAIL_PASS  "Gmail App Password" ""
    ask TELEGRAM_TOKEN   "Telegram bot token" ""
    ask TELEGRAM_CHAT_ID "Telegram chat ID (your user ID)" ""
    ask ANGEL_PORT  "Port for Angel MCP service" "39571"
    ask ANGEL_REPO  "Angel GitHub repo URL" ""
    ask ANGEL_MODEL "Angel AI model (google/anthropic/openai)" "google"
    ask ANGEL_API_KEY "Angel AI API key" ""
    ask OWNER_EMAIL "Your email address (for CC on outbound mail)" ""

    # Write config.env
    cat > "$CONFIG_FILE" << ENVFILE
BASE_DIR=$BASE_DIR
COS_USER=$COS_USER
BASE_URL=$BASE_URL
DB_NAME=$DB_NAME
TZ=$TZ
GMAIL_USER=$GMAIL_USER
GMAIL_PASS=$GMAIL_PASS
ALERT_SCRIPT=$BASE_DIR/scripts/utils/send_alert.sh
TELEGRAM_TOKEN=$TELEGRAM_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID
ANGEL_PORT=$ANGEL_PORT
ANGEL_REPO=$ANGEL_REPO
ANGEL_MODEL=$ANGEL_MODEL
ANGEL_API_KEY=$ANGEL_API_KEY
OWNER_EMAIL=$OWNER_EMAIL
ENVFILE
    ok "config.env written"
fi

# Validate required vars
for var in BASE_DIR COS_USER BASE_URL DB_NAME TELEGRAM_TOKEN TELEGRAM_CHAT_ID ANGEL_PORT; do
    [[ -z "${!var:-}" ]] && fail "$var is not set in config.env"
done

DB_PATH="$BASE_DIR/$DB_NAME"

ok "Config loaded"
echo ""
echo "  BASE_DIR:   $BASE_DIR"
echo "  COS_USER:   $COS_USER"
echo "  BASE_URL:   $BASE_URL"
echo "  DB_NAME:    $DB_NAME"
echo "  TZ:         ${TZ:-America/New_York}"
echo "  ANGEL_PORT: $ANGEL_PORT"

# Show server IP and DNS reminder if a domain is configured
if echo "$BASE_URL" | grep -qP '^[a-zA-Z]'; then
    PUBLIC_IP=$(curl -sf --max-time 5 https://api.ipify.org 2>/dev/null || \
                curl -sf --max-time 5 https://ifconfig.me 2>/dev/null || \
                hostname -I | awk '{print $1}')
    echo ""
    echo "  Server IP: $PUBLIC_IP"
    echo "  ${WARN} Make sure $BASE_URL → $PUBLIC_IP is set in your DNS before Nginx/SSL runs."
    echo "  If not done yet, do it now — SSL (Step 10) requires the domain to be resolving."
fi

# -------------------------------------------------------
# STEP 2 — Create system user and directories
# -------------------------------------------------------
step "Create user and directory structure"

# Create user if not exists
if id "$COS_USER" &>/dev/null; then
    warn "User '$COS_USER' already exists — skipping user creation"
else
    sudo useradd -m -s /bin/bash "$COS_USER"
    ok "User '$COS_USER' created"
fi

# Create directory structure
sudo -u "$COS_USER" mkdir -p \
    "$BASE_DIR/scripts/core" \
    "$BASE_DIR/scripts/alerts" \
    "$BASE_DIR/scripts/utils" \
    "$BASE_DIR/scripts/wiki" \
    "$BASE_DIR/www/HQ" \
    "$BASE_DIR/memory/archives" \
    "$BASE_DIR/logs" \
    "$BASE_DIR/skills" \
    "$BASE_DIR/wiki/research" \
    "$BASE_DIR/wiki/concepts" \
    "$BASE_DIR/wiki/entities" \
    "$BASE_DIR/wiki/topics" \
    "$BASE_DIR/raw"

verify "Directory structure created" "[ -d '$BASE_DIR/scripts/core' ]"
verify "Logs directory created"      "[ -d '$BASE_DIR/logs' ]"
verify "Memory directory created"    "[ -d '$BASE_DIR/memory' ]"

# -------------------------------------------------------
# STEP 3 — Deploy and configure scripts
# -------------------------------------------------------
step "Deploy scripts"

# Copy scripts
sudo cp -r "$CHIEFOS_SRC/scripts/." "$BASE_DIR/scripts/"

# Apply config variable substitutions via sed
# Replace placeholder paths with actual config values
find "$BASE_DIR/scripts" -type f \( -name "*.py" -o -name "*.sh" \) | while read f; do
    sudo sed -i \
        -e "s|/home/chiefos/chiefos|$BASE_DIR|g" \
        -e "s|chiefos\.db|$DB_NAME|g" \
        -e "s|yourdomain\.com|$BASE_URL|g" \
        "$f"
done

# Write .env file to BASE_DIR
sudo -u "$COS_USER" tee "$BASE_DIR/.env" > /dev/null << ENVFILE
BASE_DIR=$BASE_DIR
COS_USER=$COS_USER
BASE_URL=$BASE_URL
DB_NAME=$DB_NAME
TZ=${TZ:-America/New_York}
GMAIL_USER=${GMAIL_USER:-}
GMAIL_PASS=${GMAIL_PASS:-}
ALERT_SCRIPT=$BASE_DIR/scripts/utils/send_alert.sh
TELEGRAM_TOKEN=${TELEGRAM_TOKEN:-}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID:-}
ANGEL_PORT=$ANGEL_PORT
OWNER_EMAIL=${OWNER_EMAIL:-}
ENVFILE

sudo chmod 600 "$BASE_DIR/.env"
sudo chown "$COS_USER:$COS_USER" "$BASE_DIR/.env"

# Install Python dependencies
if [[ -f "$CHIEFOS_SRC/requirements.txt" ]]; then
    sudo -u "$COS_USER" pip3 install -r "$CHIEFOS_SRC/requirements.txt" --quiet
    ok "Python dependencies installed (requirements.txt)"
fi

# Make all scripts executable
sudo find "$BASE_DIR/scripts" -name "*.sh" -o -name "*.py" | xargs sudo chmod +x

# Spot-check: verify key scripts present and no placeholder paths remain
verify "add_todo.py deployed"        "[ -f '$BASE_DIR/scripts/core/add_todo.py' ]"
verify "master_hydration.sh deployed" "[ -f '$BASE_DIR/scripts/core/master_hydration.sh' ]"
verify "send_alert.sh deployed"      "[ -f '$BASE_DIR/scripts/utils/send_alert.sh' ]"
verify "load_env.sh deployed"        "[ -f '$BASE_DIR/scripts/utils/load_env.sh' ]"

# Verify no placeholder paths remain
PLACEHOLDER_COUNT=$(grep -r "/home/chiefos/chiefos" "$BASE_DIR/scripts/" 2>/dev/null | wc -l || echo 0)
[[ "$PLACEHOLDER_COUNT" -gt 0 ]] && warn "$PLACEHOLDER_COUNT placeholder paths remain — may need manual fix" || ok "No placeholder paths remaining"

SCRIPT_COUNT=$(find "$BASE_DIR/scripts" -name "*.py" -o -name "*.sh" | wc -l)
ok "$SCRIPT_COUNT scripts deployed and configured"

# -------------------------------------------------------
# STEP 4 — Initialize wiki knowledge base
# -------------------------------------------------------
step "Initialize wiki knowledge base"

for seed_file in index.md log.md hot.md; do
    DEST="$BASE_DIR/wiki/$seed_file"
    if [[ -f "$DEST" ]]; then
        warn "$seed_file already exists — skipping (existing wiki preserved)"
    else
        sudo -u "$COS_USER" cp "$CHIEFOS_SRC/setup/wiki/$seed_file" "$DEST"
        ok "$seed_file created"
    fi
done

sudo find "$BASE_DIR/scripts/wiki" -name "*.sh" -exec chmod +x {} \;

verify "Wiki directory ready"   "[ -d '$BASE_DIR/wiki' ]"
verify "Raw directory ready"    "[ -d '$BASE_DIR/raw' ]"
verify "Wiki index present"     "[ -f '$BASE_DIR/wiki/index.md' ]"
ok "Drop files into $BASE_DIR/raw/ and ask your agent to ingest them"

# -------------------------------------------------------
# STEP 5 — Initialize database
# -------------------------------------------------------
step "Initialize database"

if [[ -f "$DB_PATH" ]]; then
    warn "Database already exists at $DB_PATH — skipping init (existing data preserved)"
else
    sudo -u "$COS_USER" sqlite3 "$DB_PATH" < "$CHIEFOS_SRC/setup/schema.sql"
    ok "Schema applied (25 tables)"

    sudo -u "$COS_USER" sqlite3 "$DB_PATH" < "$CHIEFOS_SRC/setup/seed_data.sql"
    ok "Seed data loaded"
fi

# Verify
bash "$CHIEFOS_SRC/setup/verify_db.sh" "$DB_PATH"

# -------------------------------------------------------
# STEP 6 — Deploy HQ dashboards
# -------------------------------------------------------
step "Deploy HQ dashboards"

sudo cp -r "$CHIEFOS_SRC/www/HQ/." "$BASE_DIR/www/HQ/"

# Substitute domain in HTML
find "$BASE_DIR/www/HQ" -name "*.html" -exec sudo sed -i \
    -e "s|your\.domain\.com|$BASE_URL|g" \
    -e "s|yourdomain\.com|$BASE_URL|g" \
    {} \;

# Create empty JSON data files so dashboards load without errors
for domain in finance property schedule posts security weekly_layout; do
    DATA_FILE="$BASE_DIR/www/HQ/$domain/${domain}_data.json"
    [[ "$domain" == "posts" ]] && DATA_FILE="$BASE_DIR/www/HQ/posts/posts_data.json"
    [[ "$domain" == "weekly_layout" ]] && DATA_FILE="$BASE_DIR/www/HQ/weekly_layout/index.html" && continue
    if [[ ! -f "$DATA_FILE" ]]; then
        sudo -u "$COS_USER" bash -c "echo '{}' > '$DATA_FILE'"
        sudo chmod o+w "$DATA_FILE"
    fi
done

# Set permissions so Nginx (www-data) can read the files
sudo find "$BASE_DIR/www" -type d -exec chmod 755 {} \;
sudo find "$BASE_DIR/www" -type f -exec chmod 644 {} \;
sudo chown -R "$COS_USER:$COS_USER" "$BASE_DIR/www"

# Verify pages present
PAGE_COUNT=$(find "$BASE_DIR/www/HQ" -name "index.html" | wc -l)
verify "Dashboard pages deployed ($PAGE_COUNT pages)" "[ '$PAGE_COUNT' -ge 7 ]"
verify "www/ permissions set for Nginx" "[ -r '$BASE_DIR/www/HQ/index.html' ]"

# -------------------------------------------------------
# STEP 7 — Deploy governance files
# -------------------------------------------------------
step "Deploy governance files (SOUL, TOOLS, AGENTS)"

# Check for existing OpenClaw workspace
if [[ -f "$BASE_DIR/SOUL.md" ]]; then
    warn "Existing SOUL.md found — running OpenClaw patch instead of overwrite"
    bash "$CHIEFOS_SRC/openclaw/patch_openclaw.sh" "$BASE_DIR" "$CHIEFOS_SRC"
else
    sudo -u "$COS_USER" cp "$CHIEFOS_SRC/config/SOUL_template.md"   "$BASE_DIR/SOUL.md"
    sudo -u "$COS_USER" cp "$CHIEFOS_SRC/config/TOOLS_template.md"  "$BASE_DIR/TOOLS.md"
    sudo -u "$COS_USER" cp "$CHIEFOS_SRC/config/AGENTS_template.md" "$BASE_DIR/AGENTS.md"

    # Substitute placeholders
    for f in "$BASE_DIR/SOUL.md" "$BASE_DIR/TOOLS.md" "$BASE_DIR/AGENTS.md"; do
        sudo sed -i \
            -e "s|\$BASE_DIR|$BASE_DIR|g" \
            -e "s|\$DB_NAME|$DB_NAME|g" \
            -e "s|\[BASE_DIR\]|$BASE_DIR|g" \
            -e "s|\[DB_NAME\]|$DB_NAME|g" \
            -e "s|\[ANGEL_PORT\]|$ANGEL_PORT|g" \
            "$f"
    done

    ok "SOUL.md deployed"
    ok "TOOLS.md deployed"
    ok "AGENTS.md deployed"
fi

verify "SOUL.md present"   "[ -f '$BASE_DIR/SOUL.md' ]"
verify "TOOLS.md present"  "[ -f '$BASE_DIR/TOOLS.md' ]"
verify "AGENTS.md present" "[ -f '$BASE_DIR/AGENTS.md' ]"

warn "ACTION REQUIRED: Edit $BASE_DIR/SOUL.md — replace [YOUR_AGENT_NAME] and [YOUR_NAME]"

# -------------------------------------------------------
# STEP 8 — Install Angel
# -------------------------------------------------------
step "Install Angel (governance service)"

if [[ -d "/home/angel/angel" ]]; then
    warn "Existing Angel installation detected at /home/angel/angel"
    warn "Skipping Angel install — verify she is running before continuing"
    echo ""
    echo "  To check Angel status:"
    echo "    curl -s http://127.0.0.1:$ANGEL_PORT/mcp"
    echo "    sudo -u angel pm2 list"
else
    # Create angel user
    if id "angel" &>/dev/null; then
        warn "User 'angel' already exists"
    else
        sudo useradd -m -s /bin/bash angel
        ok "User 'angel' created"
    fi

    # Install PM2 globally if not present
    if ! command -v pm2 &>/dev/null; then
        sudo npm install -g pm2
        ok "PM2 installed"
    fi

    # Clone Angel's repo
    [[ -z "${ANGEL_REPO:-}" ]] && fail "ANGEL_REPO is not set in config.env — cannot install Angel"

    sudo -u angel git clone "$ANGEL_REPO" /home/angel/angel
    verify "Angel repo cloned" "[ -d '/home/angel/angel' ]"

    # Configure Angel
    if [[ -f "/home/angel/angel/.env.template" ]]; then
        sudo -u angel cp /home/angel/angel/.env.template /home/angel/angel/.env
    else
        sudo -u angel touch /home/angel/angel/.env
    fi

    # Write Angel config
    sudo -u angel tee /home/angel/angel/.env > /dev/null << ANGEL_ENV
ANGEL_MODEL=${ANGEL_MODEL:-google}
ANGEL_API_KEY=${ANGEL_API_KEY:-}
ANGEL_PORT=$ANGEL_PORT
ANGEL_ENV
    sudo chmod 600 /home/angel/angel/.env

    # Build Angel
    sudo -u angel bash -c "cd /home/angel/angel && npm install"
    sudo -u angel bash -c "cd /home/angel/angel && npm run build" 2>/dev/null || warn "npm run build failed — Angel may use a different build step"

    verify "Angel build output exists" "[ -f '/home/angel/angel/dist/index.js' ] || [ -f '/home/angel/angel/index.js' ]"

    # Determine entrypoint
    if [[ -f "/home/angel/angel/dist/index.js" ]]; then
        ANGEL_ENTRY="/home/angel/angel/dist/index.js"
    else
        ANGEL_ENTRY="/home/angel/angel/index.js"
    fi

    # Start via PM2
    sudo -u angel bash -c "pm2 start '$ANGEL_ENTRY' --name angel"
    sudo -u angel bash -c "pm2 save"
    ok "Angel started via PM2"

    # Configure PM2 to survive server reboots
    PM2_STARTUP=$(sudo -u angel bash -c "pm2 startup systemd -u angel --hp /home/angel 2>&1 | grep 'sudo' | tail -1" || true)
    if [[ -n "$PM2_STARTUP" ]]; then
        eval "$PM2_STARTUP" 2>/dev/null || true
    else
        sudo env PATH="$PATH:/usr/bin" pm2 startup systemd -u angel --hp /home/angel 2>/dev/null || true
    fi
    sudo systemctl enable pm2-angel 2>/dev/null || true
    ok "Angel configured to start on reboot (pm2 startup)"

    # Verify MCP endpoint
    sleep 3
    if curl -sf --max-time 5 "http://127.0.0.1:$ANGEL_PORT/mcp" > /dev/null 2>&1; then
        ok "MCP endpoint responding at http://127.0.0.1:$ANGEL_PORT/mcp"
    else
        warn "MCP endpoint not yet responding — Angel may still be starting"
        warn "Check with: curl http://127.0.0.1:$ANGEL_PORT/mcp"
    fi

    # Deploy Angel skill file
    mkdir -p "$BASE_DIR/skills/angel-guardian"
    cat > "$BASE_DIR/skills/angel-guardian/SKILL.md" << SKILL
# Angel Guardian Skill

Angel is the governance layer for ChiefOS. She runs as a separate OS user
and independently authorizes all consequential actions.

## MCP Endpoint
http://127.0.0.1:$ANGEL_PORT/mcp

## Tool
angel.verify_action_plan

## Usage
Submit every Tier 4+ action before execution. See SOUL.md §5 for full protocol.
SKILL
    ok "Angel skill file deployed to $BASE_DIR/skills/angel-guardian/SKILL.md"
fi

# -------------------------------------------------------
# STEP 9 — Install crontab
# -------------------------------------------------------
step "Install crontab"

# Calculate UTC offset from timezone
TZ_ENV="${TZ:-America/New_York}"
UTC_OFFSET=$(python3 -c "
import datetime, zoneinfo
tz = zoneinfo.ZoneInfo('$TZ_ENV')
now = datetime.datetime.now(tz)
offset_hours = int(now.utcoffset().total_seconds() / 3600)
print(-offset_hours)
" 2>/dev/null || echo "5")

echo "  Timezone: $TZ_ENV (UTC offset: UTC-${UTC_OFFSET}h → adding ${UTC_OFFSET}h to convert to UTC)"
echo ""

# Helper to convert local hour to UTC cron hour
utc_hour() {
    local local_h="$1"
    echo $(( (local_h + UTC_OFFSET) % 24 ))
}

H_400=$(utc_hour 4)    # 4:00am local  = briefing engine
H_215=$(utc_hour 2)    # 2:15am local  = master hydration (using 2 as approximate)
H_500=$(utc_hour 5)    # 5:00am local  = alert scripts
H_530=$(utc_hour 5)    # 5:30am local  = todo alert (minute=30)
H_545=$(utc_hour 5)    # 5:45am local  = weekly preview (minute=45)
H_900=$(utc_hour 9)    # 9:00am local  = project status (Monday)
H_SEV=$(utc_hour 7)    # 7:00am local  = security monitor
H_12=$(utc_hour 12)    # 12:00pm local = security monitor
H_20=$(utc_hour 20)    # 8:00pm local  = security monitor + sunday preview

CRON_FILE=$(mktemp)
cat > "$CRON_FILE" << CRONTAB
# ============================================================
# ChiefOS Crontab
# All times in UTC. Local timezone: $TZ_ENV (UTC+${UTC_OFFSET}h)
# ============================================================

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# --- Briefing Engine (4:00am local) ---
0 $H_400 * * * cd $BASE_DIR && source .env && python3 scripts/core/daily_briefing_v11.py >> logs/cron.log 2>&1

# --- Master Hydration (2:15am local) ---
15 $(utc_hour 2) * * * cd $BASE_DIR && bash scripts/core/master_hydration.sh >> logs/hydration.log 2>&1

# --- Alert Scripts (5:00am local) ---
0 $H_500 * * * cd $BASE_DIR && source .env && python3 scripts/alerts/bill_reminder.py >> logs/cron.log 2>&1
0 $H_500 * * * cd $BASE_DIR && source .env && python3 scripts/alerts/deposit_reminder.py >> logs/cron.log 2>&1
0 $H_500 * * * cd $BASE_DIR && source .env && python3 scripts/alerts/maintenance_tracker.py >> logs/cron.log 2>&1
0 $H_500 * * * cd $BASE_DIR && source .env && python3 scripts/alerts/morning_email_review.py >> logs/cron.log 2>&1

# --- Todo Alert (5:30am local) ---
30 $H_530 * * * cd $BASE_DIR && source .env && python3 scripts/alerts/todo_alert.py >> logs/cron.log 2>&1

# --- Weekly Preview (5:45am daily + Sunday 8pm local) ---
45 $H_545 * * * cd $BASE_DIR && source .env && python3 scripts/alerts/weekly_preview.py >> logs/cron.log 2>&1
0 $H_20 * * 0  cd $BASE_DIR && source .env && python3 scripts/alerts/weekly_preview.py >> logs/cron.log 2>&1

# --- Project Status (Monday 9:00am local) ---
0 $H_900 * * 1 cd $BASE_DIR && source .env && python3 scripts/alerts/project_status.py >> logs/cron.log 2>&1

# --- Monthly Summary (last day of month 9pm local — approximated as 1st of month 2am UTC) ---
0 $(utc_hour 21) 28-31 * * cd $BASE_DIR && source .env && python3 scripts/alerts/monthly_summary.py >> logs/cron.log 2>&1

# --- Security Monitor (7am, 12pm, 8pm local) ---
0 $H_SEV * * * bash $BASE_DIR/scripts/utils/cron-security-monitor.sh >> logs/security.log 2>&1
0 $H_12  * * * bash $BASE_DIR/scripts/utils/cron-security-monitor.sh >> logs/security.log 2>&1
0 $H_20  * * * bash $BASE_DIR/scripts/utils/cron-security-monitor.sh >> logs/security.log 2>&1

# --- Executive Security Summary (4:15pm local) ---
15 $(utc_hour 16) * * * bash $BASE_DIR/scripts/utils/executive-security-summary.sh >> logs/security.log 2>&1

# --- Email Check (every 30 minutes) ---
*/30 * * * * cd $BASE_DIR && source .env && python3 scripts/utils/check_emails.py >> logs/email_check.log 2>&1
CRONTAB

sudo crontab -u "$COS_USER" "$CRON_FILE"
rm "$CRON_FILE"

# Verify
CRON_LINES=$(sudo crontab -u "$COS_USER" -l | grep -v "^#" | grep -v "^$" | wc -l)
verify "Crontab installed ($CRON_LINES active jobs)" "[ '$CRON_LINES' -ge 10 ]"

# -------------------------------------------------------
# STEP 10 — First hydration
# -------------------------------------------------------
step "First hydration (generate dashboard data)"

sudo -u "$COS_USER" bash "$BASE_DIR/scripts/core/master_hydration.sh" || {
    warn "Hydration encountered errors — dashboards may show partial data"
    warn "Run manually: sudo -u $COS_USER bash $BASE_DIR/scripts/core/master_hydration.sh"
}

JSON_COUNT=$(find "$BASE_DIR/www/HQ" -name "*.json" | wc -l)
ok "Hydration complete ($JSON_COUNT data files generated)"

# -------------------------------------------------------
# STEP 11 — Nginx + SSL + Firewall
# -------------------------------------------------------
step "Web server, SSL, and firewall"

# Install Nginx if missing
if ! command -v nginx &>/dev/null; then
    ok "Installing Nginx..."
    sudo apt-get install -y nginx -q
fi

# Deploy Nginx config from template
NGINX_CONF="/etc/nginx/sites-available/chiefos"
sudo cp "$CHIEFOS_SRC/config/nginx-chiefos.conf.template" "$NGINX_CONF"
sudo sed -i \
    -e "s|CHIEFOS_DOMAIN|$BASE_URL|g" \
    -e "s|CHIEFOS_WEBROOT|$BASE_DIR/www|g" \
    "$NGINX_CONF"
sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/chiefos
# Remove default site if present
sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
sudo nginx -t && sudo systemctl reload nginx
ok "Nginx configured and reloaded"
verify "Nginx serving ChiefOS" "sudo nginx -t"

# Open firewall ports
if command -v ufw &>/dev/null; then
    UFW_STATUS=$(sudo ufw status 2>/dev/null | head -1)
    if echo "$UFW_STATUS" | grep -q "active"; then
        sudo ufw allow 80/tcp  > /dev/null 2>&1
        sudo ufw allow 443/tcp > /dev/null 2>&1
        ok "Firewall: ports 80 and 443 opened"
    else
        warn "UFW is inactive — skipping firewall rules"
    fi
else
    warn "UFW not found — ensure ports 80/443 are open in your cloud provider's security group"
fi

# SSL via Certbot (optional — skip if no email or domain looks like an IP)
if [[ -n "${OWNER_EMAIL:-}" ]] && echo "$BASE_URL" | grep -qP '^[a-zA-Z]'; then
    if ! command -v certbot &>/dev/null; then
        sudo apt-get install -y certbot python3-certbot-nginx -q 2>/dev/null || true
    fi
    if command -v certbot &>/dev/null; then
        sudo certbot --nginx -d "$BASE_URL" --non-interactive \
            --agree-tos -m "$OWNER_EMAIL" --redirect 2>/dev/null \
            && ok "SSL certificate installed via Certbot" \
            || warn "Certbot SSL failed — run manually: sudo certbot --nginx -d $BASE_URL"
    fi
else
    warn "Skipping SSL — set OWNER_EMAIL and use a real domain to enable auto-SSL"
fi

# -------------------------------------------------------
# STEP 12 — Log rotation
# -------------------------------------------------------
step "Log rotation"

sudo cp "$CHIEFOS_SRC/config/logrotate-chiefos" /etc/logrotate.d/chiefos
sudo sed -i \
    -e "s|CHIEFOS_LOGS_DIR|$BASE_DIR/logs|g" \
    -e "s|CHIEFOS_USER|$COS_USER|g" \
    /etc/logrotate.d/chiefos
ok "Log rotation configured (14 days, daily, compressed)"

# -------------------------------------------------------
# FINAL HEALTH CHECK
# -------------------------------------------------------
step "Final health check"

HEALTH_ISSUES=0

# Web UI reachable via Nginx
if curl -sf --max-time 5 "http://127.0.0.1/HQ/" > /dev/null 2>&1; then
    ok "Web UI reachable at http://$BASE_URL/HQ/"
else
    warn "Web UI not yet reachable locally — Nginx may need a moment"
    warn "Check with: sudo systemctl status nginx"
    HEALTH_ISSUES=$((HEALTH_ISSUES + 1))
fi

# Angel MCP endpoint
if curl -sf --max-time 5 "http://127.0.0.1:$ANGEL_PORT/mcp" > /dev/null 2>&1; then
    ok "Angel MCP endpoint responding at http://127.0.0.1:$ANGEL_PORT/mcp"
else
    warn "Angel MCP endpoint not yet responding"
    warn "Check with: sudo -u angel pm2 list"
    HEALTH_ISSUES=$((HEALTH_ISSUES + 1))
fi

# Database tables
TABLE_COUNT=$(sqlite3 "$DB_PATH" "SELECT count(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo 0)
if [[ "$TABLE_COUNT" -ge 25 ]]; then
    ok "Database: $TABLE_COUNT tables confirmed"
else
    warn "Database has only $TABLE_COUNT tables — expected 25+"
    warn "Re-run: bash $CHIEFOS_SRC/setup/verify_db.sh $DB_PATH"
    HEALTH_ISSUES=$((HEALTH_ISSUES + 1))
fi

# Crontab installed
CRON_FINAL=$(sudo crontab -u "$COS_USER" -l 2>/dev/null | grep -v "^#" | grep -v "^$" | wc -l || echo 0)
if [[ "$CRON_FINAL" -ge 10 ]]; then
    ok "Crontab: $CRON_FINAL jobs scheduled"
else
    warn "Crontab has only $CRON_FINAL active jobs — check: sudo crontab -u $COS_USER -l"
    HEALTH_ISSUES=$((HEALTH_ISSUES + 1))
fi

# Dashboard data files
JSON_FINAL=$(find "$BASE_DIR/www/HQ" -name "*.json" 2>/dev/null | wc -l || echo 0)
if [[ "$JSON_FINAL" -ge 3 ]]; then
    ok "Dashboard data: $JSON_FINAL JSON files present"
else
    warn "Dashboard data files missing — run hydration manually:"
    warn "  sudo -u $COS_USER bash $BASE_DIR/scripts/core/master_hydration.sh"
    HEALTH_ISSUES=$((HEALTH_ISSUES + 1))
fi

if [[ "$HEALTH_ISSUES" -eq 0 ]]; then
    ok "All health checks passed — system is operational"
else
    warn "$HEALTH_ISSUES health check(s) need attention — see warnings above"
fi

echo ""
echo "  Logs directory: $BASE_DIR/logs/"
echo "  Re-check health at any time: bash verify-install.sh"

# -------------------------------------------------------
# FINAL SUMMARY
# -------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║      ChiefOS Installation Complete!      ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Workspace:   $BASE_DIR"
echo "  Database:    $DB_PATH"
echo "  Dashboards:  http://$BASE_URL/HQ/"
echo "  Briefing:    http://$BASE_URL/HQ/briefing/"
echo ""
echo "Next steps:"
echo ""
echo "  1. Edit your agent identity:"
echo "     $BASE_DIR/SOUL.md — replace [YOUR_AGENT_NAME] and [YOUR_NAME]"
echo ""
echo "  2. Open your HQ:  http://$BASE_URL/HQ/"
echo ""
echo "  3. Point your AI platform to ChiefOS:"
echo "     - Set working directory to: $BASE_DIR"
echo "     - Load SOUL.md as system prompt"
echo "     - Load TOOLS.md and AGENTS.md as context"
echo "     - Configure MCP server: http://127.0.0.1:$ANGEL_PORT/mcp"
echo ""
echo "  4. Add your first todo:"
echo "     python3 $BASE_DIR/scripts/core/add_todo.py \\"
echo "       --title 'My first task' --category personal --priority high \\"
echo "       --due_date $(date -d '+7 days' +%Y-%m-%d 2>/dev/null || date -v+7d +%Y-%m-%d)"
echo ""
echo "  See docs/SETUP.md for full configuration guide."
echo ""
