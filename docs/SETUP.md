# ChiefOS Setup Guide

Step-by-step instructions for a complete ChiefOS installation on a fresh Ubuntu/Debian server.

---

## Before You Start — Prerequisite Checklist

Collect these **before** opening `config.env`. The install will ask for all of them.

| What | How to get it | Used for |
|---|---|---|
| ☐ **Telegram bot token** | Message `@BotFather` on Telegram → `/newbot` → copy the token | All alerts |
| ☐ **Telegram Chat ID** | Message `@userinfobot` on Telegram → copy the number | Receiving alerts |
| ☐ **Gmail App Password** | [Google Account → Security → App Passwords](https://support.google.com/accounts/answer/185833) (requires 2FA enabled) | Email monitoring |
| ☐ **Angel repo URL** | GitHub URL of your Angel governance service | Agent governance |
| ☐ **Angel API key** | API key for your chosen model (Google, Anthropic, or OpenAI) | Angel's AI model |
| ☐ **Domain or server IP** | Your VPS IP address, or a domain pointing to it | Dashboard access |

> **Don't have Angel yet?** Leave `ANGEL_REPO` blank in `config.env` for now — you can configure it later. ChiefOS will install without it, but the governance layer won't be active.

---

## Server Requirements

- Ubuntu 20.04+ or Debian 11+
- 1GB RAM minimum, 10GB disk
- sudo access
- Ports 80 and 443 open (or configured in your cloud provider's firewall)

---

## Step 1 — Install Node.js 18+

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version  # should be v20.x.x
```

---

## Step 2 — Clone ChiefOS

```bash
git clone https://github.com/YOUR/CHIEFOS.git
cd CHIEFOS
```

---

## Step 3 — Configure

```bash
cp config.env.template config.env
nano config.env
```

Fill in every `✅ REQUIRED` value. Key ones:

```bash
BASE_DIR=/home/chiefos/chiefos    # Where ChiefOS will live
COS_USER=chiefos                  # OS user to create
BASE_URL=yourdomain.com           # Your domain (no http://)
TZ=America/New_York               # Your timezone
TELEGRAM_TOKEN=your_bot_token     # From @BotFather
TELEGRAM_CHAT_ID=your_chat_id     # From @userinfobot
ANGEL_REPO=https://github.com/YOUR/angel-repo
ANGEL_MODEL=google                # google | anthropic | openai
ANGEL_API_KEY=your_api_key
```

See `docs/CONFIGURATION.md` for every variable explained in detail.

**Security tip:** Lock down your config file once filled in:
```bash
chmod 600 config.env
```

---

## Step 4 — Run Preflight

Verifies your machine meets all requirements before anything is installed:

```bash
bash preflight.sh
```

Fix any `❌` blockers before continuing. `⚠️` warnings are handled automatically by the installer.

---

## Step 5 — Install

```bash
bash install.sh
```

The installer walks through 11 steps with verification after each one:

1. Configuration — reads `config.env`, prompts interactively if missing
2. User + directories — creates the `$COS_USER` OS user and workspace
3. Scripts — deploys and configures all Python/Bash scripts
4. Database — applies the 27-table schema and seeds demo data
5. Dashboards — deploys 8 HTML dashboards to `www/HQ/`
6. Governance files — deploys `SOUL.md`, `TOOLS.md`, `AGENTS.md`
7. Angel — installs the governance service as a separate OS user
8. Crontab — installs all scheduled jobs (timezone-adjusted to UTC)
9. Hydration — runs first data generation so dashboards aren't empty
10. Nginx + SSL — configures web server and optionally installs Certbot certificate
11. Log rotation — sets up 14-day rolling logs

Estimated time: **5–10 minutes**

If something fails mid-install, fix the issue and re-run `bash install.sh` — most steps are idempotent.

All logs are written to `$BASE_DIR/logs/` throughout the install.

---

## Step 6 — Verify the Installation

After install completes, run the built-in verification script:

```bash
bash verify-install.sh
```

This checks that the web UI, Angel, database, crontab, and dashboards are all operational.

You can also check manually:

```bash
# Source your environment first
source $BASE_DIR/.env

# Check Angel is running
curl -s http://127.0.0.1:$ANGEL_PORT/mcp | head -5

# Run a manual hydration
sudo -u $COS_USER bash $BASE_DIR/scripts/core/master_hydration.sh

# Check crontab
sudo crontab -u $COS_USER -l

# Check logs
tail -50 $BASE_DIR/logs/cron.log
```

---

## Step 6.5 — Set Up Obsidian Wiki Visualization (Optional but Recommended)

The wiki lives as markdown files on your server. Obsidian lets you browse it visually on your local machine — with a graph view showing how all pages connect, live link navigation, and full-text search.

### Part A — Install rclone (syncs wiki to cloud)

On your server:
```bash
# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Configure your cloud provider (Google Drive, Dropbox, S3, etc.)
rclone config
# → Choose "n" for new remote
# → Give it a name: gdrive (or dropbox, etc.)
# → Follow the prompts for your provider
# → When done, test: rclone ls gdrive:
```

Then add to `config.env`:
```bash
RCLONE_REMOTE=gdrive                  # name you gave during rclone config
RCLONE_WIKI_PATH=MyDrive/ChiefOS      # folder path in your cloud storage
```

ChiefOS will sync `wiki/` and `raw/` to the cloud every 15 minutes automatically via cron.

Manual sync at any time:
```bash
source $BASE_DIR/.env
bash $BASE_DIR/scripts/wiki/sync_wiki.sh
```

### Part B — Set Up Obsidian

1. Download [Obsidian](https://obsidian.md/) on your Mac/PC/phone — it's free
2. Install [Google Drive for Desktop](https://www.google.com/drive/download/) (or your cloud app) so the synced folder appears locally
3. In Obsidian: **File → Open Vault** → navigate to your synced `wiki/` folder → **Open**

That's it. Obsidian will index all your wiki pages and you'll have:
- **Graph View** (left sidebar `Ctrl+G`) — visual map of all pages and their connections
- **Backlinks** — see what links to any page
- **Live `[[link]]` navigation** — click any link to jump to that page

### Part C — Recommended Obsidian Plugins

In Obsidian: **Settings → Community Plugins → Browse**

| Plugin | Why |
|---|---|
| **Dataview** | Query wiki pages by frontmatter tags — e.g. show all `category: research` pages sorted by date |
| **Obsidian Web Clipper** | Browser extension — clips any web article to your `raw/` folder in one click |

### Using the Wiki

**Add a new source:**
```bash
# Option 1: Drop a file directly into raw/
cp ~/Downloads/article.md $BASE_DIR/raw/

# Option 2: Use Obsidian Web Clipper in your browser → saves to raw/ via cloud sync

# Then tell your agent:
# "Ingest $BASE_DIR/raw/article.md into the wiki"
```

**Search the wiki:**
```bash
source $BASE_DIR/.env
bash $BASE_DIR/scripts/wiki/search_wiki.sh "mortgage rates"
```

**Lint (health check):**
```bash
bash $BASE_DIR/scripts/wiki/lint_wiki.sh
```

---

## Step 7 — Configure Your AI Agent

Point your AI platform to ChiefOS:

1. **Working directory:** `$BASE_DIR` (e.g. `/home/chiefos/chiefos`)
2. **System prompt / SOUL:** load `$BASE_DIR/SOUL.md`
3. **Context files:** load `$BASE_DIR/TOOLS.md` and `$BASE_DIR/AGENTS.md`
4. **MCP server:** add `http://127.0.0.1:$ANGEL_PORT/mcp` as an MCP endpoint

Then personalize your agent identity:

```bash
nano $BASE_DIR/SOUL.md
# Replace [YOUR_AGENT_NAME] with a name (e.g. "Nova")
# Replace [YOUR_NAME] with your name or preferred address
```

> **What is MCP?** The Model Context Protocol lets your AI agent communicate with Angel for governance checks. If your AI platform doesn't support MCP, ChiefOS still works — Angel just won't intercept actions.

---

## Step 8 — Add Your First Todo

```bash
source $BASE_DIR/.env
python3 $BASE_DIR/scripts/core/add_todo.py \
  --title "Welcome to ChiefOS" \
  --category personal \
  --priority high \
  --due_date $(date -d '+1 day' +%Y-%m-%d)
```

Visit `http://yourdomain.com/HQ/schedule/` — your todo should appear on the calendar.

---

## Troubleshooting

**Dashboards show no data**
```bash
source $BASE_DIR/.env
sudo -u $COS_USER bash $BASE_DIR/scripts/core/master_hydration.sh
```

**Telegram alerts not arriving**
```bash
# Test manually
echo "Test alert" > /tmp/test_msg.txt
source $BASE_DIR/.env
bash $BASE_DIR/scripts/utils/send_alert.sh /tmp/test_msg.txt
```

**Angel not responding**
```bash
sudo -u angel pm2 list
sudo -u angel pm2 logs angel --lines 50
# Restart Angel if needed:
sudo -u angel pm2 restart angel
```

**Cron jobs not running**
```bash
source $BASE_DIR/.env
sudo crontab -u $COS_USER -l        # verify entries exist
sudo systemctl status cron          # verify cron daemon is running
tail -20 /var/log/syslog | grep CRON
```

**Database issues**
```bash
source $BASE_DIR/.env
bash $CHIEFOS_SRC/setup/verify_db.sh $BASE_DIR/$DB_NAME
```

**Nginx not serving**
```bash
sudo nginx -t                          # check config syntax
sudo systemctl status nginx            # check service status
sudo systemctl reload nginx            # apply config changes
cat /etc/nginx/sites-available/chiefos # view the config
```
