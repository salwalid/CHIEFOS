# ChiefOS Setup Guide

Step-by-step instructions for a complete ChiefOS installation on a fresh Ubuntu/Debian server.

---

## Prerequisites

Before you begin, you need:

1. **A server** — Ubuntu 20.04+ or Debian 11+, with at least 1GB RAM and 10GB disk
2. **A domain** — pointing to your server's IP (or just use the IP directly)
3. **sudo access** — the installer creates system users
4. **A Telegram bot** — for alerts ([how to create one](https://core.telegram.org/bots#botfather))
5. **A Gmail address** — with an [App Password](https://support.google.com/accounts/answer/185833) for email monitoring
6. **An AI API key** — for Angel's governance model (Google, Anthropic, or OpenAI)
7. **Angel's repo URL** — the GitHub URL of your Angel governance service

---

## Step 1 — Get Your Telegram Details

1. Message `@BotFather` on Telegram → `/newbot` → follow prompts → copy the **bot token**
2. Message `@userinfobot` → copy your **Chat ID** (this is your `TELEGRAM_CHAT_ID`)

---

## Step 2 — Install Node.js 18+

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version  # should be v20.x.x
```

---

## Step 3 — Clone ChiefOS

```bash
git clone https://github.com/YOUR/CHIEFOS.git
cd CHIEFOS
```

---

## Step 4 — Configure

```bash
cp config.env.template config.env
nano config.env
```

Fill in every value. Key ones:

```bash
BASE_DIR=/home/chiefos/chiefos    # Where ChiefOS will live
COS_USER=chiefos                  # OS user to create
BASE_URL=yourdomain.com           # Your domain (no http://)
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
GMAIL_USER=your@gmail.com
GMAIL_PASS=your_app_password
ANGEL_REPO=https://github.com/YOUR/angel-repo
ANGEL_MODEL=google                # google | anthropic | openai
ANGEL_API_KEY=your_api_key
```

See `docs/CONFIGURATION.md` for every variable explained.

---

## Step 5 — Run Preflight

Check that your machine meets all requirements before installing:

```bash
cp config.env.template config.env   # fill this in first
bash preflight.sh
```

Fix any `❌` blockers before continuing. `⚠️` warnings are handled automatically.

---

## Step 6 — Install

```bash
bash install.sh
```

The installer is interactive. It walks through 9 steps with verification after each one.
Estimated time: 5–10 minutes.

If something fails mid-install, fix the issue and re-run `bash install.sh` — it's idempotent for most steps.

---

## Step 7 — Configure Nginx

Serve the HQ dashboards with Nginx:

```bash
sudo apt install -y nginx
sudo nano /etc/nginx/sites-available/chiefos
```

Paste this config (replace `yourdomain.com` and `/home/chiefos/chiefos`):

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    root /home/chiefos/chiefos/www;
    index index.html;

    location /HQ/ {
        try_files $uri $uri/ /HQ/index.html;
        add_header Cache-Control "no-cache";
    }

    location / {
        return 301 /HQ/;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/chiefos /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

For HTTPS (recommended), use Certbot:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

## Step 8 — Configure Your AI Agent

Point your AI platform to ChiefOS:

1. **Working directory:** `$BASE_DIR` (e.g. `/home/chiefos/chiefos`)
2. **System prompt / SOUL:** load `$BASE_DIR/SOUL.md`
3. **Context files:** load `$BASE_DIR/TOOLS.md` and `$BASE_DIR/AGENTS.md`
4. **MCP server:** add `http://127.0.0.1:$ANGEL_PORT/mcp` as an MCP endpoint

Then edit SOUL.md to personalize:
```bash
nano $BASE_DIR/SOUL.md
# Replace [YOUR_AGENT_NAME] with a name (e.g. "Nova")
# Replace [YOUR_NAME] with your name or preferred address
```

---

## Step 9 — Add Your First Todo

```bash
python3 $BASE_DIR/scripts/core/add_todo.py \
  --title "Welcome to ChiefOS" \
  --category personal \
  --priority high \
  --due_date $(date -d '+1 day' +%Y-%m-%d)
```

Visit `http://yourdomain.com/HQ/schedule/` — your todo should appear on the calendar.

---

## Verify Everything Is Working

```bash
# Check Angel is running
curl -s http://127.0.0.1:$ANGEL_PORT/mcp | head -5

# Run a manual hydration
sudo -u chiefos bash $BASE_DIR/scripts/core/master_hydration.sh

# Check crontab
sudo crontab -u chiefos -l

# Check logs
tail -50 $BASE_DIR/logs/cron.log
```

---

## Troubleshooting

**Dashboards show no data**
```bash
sudo -u chiefos bash $BASE_DIR/scripts/core/master_hydration.sh
```

**Telegram alerts not arriving**
```bash
# Test manually
echo "Test alert" > /tmp/test_msg.txt
bash $BASE_DIR/scripts/utils/send_alert.sh /tmp/test_msg.txt
```

**Angel not responding**
```bash
sudo -u angel pm2 list
sudo -u angel pm2 logs angel --lines 50
```

**Cron jobs not running**
```bash
sudo crontab -u chiefos -l        # verify entries
sudo systemctl status cron        # verify cron daemon
tail -20 /var/log/syslog | grep CRON
```

**Database issues**
```bash
bash $BASE_DIR/setup/verify_db.sh $BASE_DIR/chiefos.db
```
