# ChiefOS Configuration Reference

All configuration lives in `config.env` at the root of the CHIEFOS directory.
Copy `config.env.template` and fill in your values. Never commit `config.env`.

---

## Core

| Variable | Required | Example | Description |
|---|---|---|---|
| `BASE_DIR` | ✅ | `/home/chiefos/chiefos` | Absolute path to ChiefOS workspace. All scripts, database, and dashboards live here. |
| `COS_USER` | ✅ | `chiefos` | OS user that owns and runs ChiefOS. Created by the installer if it doesn't exist. |
| `BASE_URL` | ✅ | `yourdomain.com` | Your domain without `http://` and without a trailing slash. Used in dashboard links and alert messages. |
| `DB_NAME` | ✅ | `chiefos.db` | SQLite database filename. Full path will be `$BASE_DIR/$DB_NAME`. |
| `TZ` | ✅ | `America/New_York` | Your timezone in IANA format. Used to calculate correct UTC offsets for crontab. [Full list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) |

---

## Email Monitoring

Used by `check_emails.py`, `morning_email_review.py`, and other email utilities.

| Variable | Required | Example | Description |
|---|---|---|---|
| `GMAIL_USER` | ✅ | `you@gmail.com` | Gmail address to monitor for incoming mail. |
| `GMAIL_PASS` | ✅ | `abcd efgh ijkl mnop` | Gmail App Password — **not your real password**. [Create one here](https://support.google.com/accounts/answer/185833). |
| `OWNER_EMAIL` | — | `you@email.com` | Your personal email, CC'd on outbound mail sent by `send_email.py`. |

---

## Alerting

Default alert channel is Telegram via the Bot API. All alert scripts call `send_alert.sh`.

| Variable | Required | Example | Description |
|---|---|---|---|
| `ALERT_SCRIPT` | ✅ | `$BASE_DIR/scripts/utils/send_alert.sh` | Path to the alert delivery script. Swap for a custom Slack/email/webhook script if needed. |
| `TELEGRAM_TOKEN` | ✅ | `123456:ABC-DEF...` | Your Telegram bot token from `@BotFather`. |
| `TELEGRAM_CHAT_ID` | ✅ | `123456789` | Your Telegram user ID (get from `@userinfobot`). |

### Swapping the alert channel

To route alerts to Slack, email, or a webhook instead of Telegram:

1. Write a script that accepts a message file path as `$1` and delivers it
2. Point `ALERT_SCRIPT` in `config.env` to your script
3. The existing `send_alert.sh` is a good reference implementation

---

## Angel (Governance Service)

Angel is the authorization layer. She runs as a separate OS user (`angel`) with her own process.

| Variable | Required | Example | Description |
|---|---|---|---|
| `ANGEL_PORT` | ✅ | `39571` | Port Angel's MCP server listens on. Must not be in use by anything else. |
| `ANGEL_REPO` | ✅ | `https://github.com/your/angel` | GitHub URL of Angel's repo. Cloned during install. |
| `ANGEL_MODEL` | ✅ | `google` | AI provider for Angel's reasoning: `google`, `anthropic`, or `openai`. |
| `ANGEL_API_KEY` | ✅ | `AIza...` | API key for the chosen `ANGEL_MODEL`. |

---

## Wiki Cloud Sync — Obsidian Access (Optional)

Syncs your wiki to cloud storage so you can browse it in Obsidian on any device.
Requires [rclone](https://rclone.org/install/) installed and a remote configured (`rclone config`).

| Variable | Required | Example | Description |
|---|---|---|---|
| `RCLONE_REMOTE` | — | `gdrive` | Name of your rclone remote (set during `rclone config`) |
| `RCLONE_WIKI_PATH` | — | `MyDrive/ChiefOS` | Folder path in cloud storage. Wiki syncs to `.../wiki/`, raw sources to `.../raw/` |

**Setup flow:**
```bash
# 1. Install rclone
curl https://rclone.org/install.sh | sudo bash

# 2. Configure your cloud provider (Google Drive, Dropbox, etc.)
rclone config
# Follow prompts → give the remote a name (e.g. "gdrive") → authenticate

# 3. Set in config.env
RCLONE_REMOTE=gdrive
RCLONE_WIKI_PATH=MyDrive/ChiefOS

# 4. In Obsidian: File → Open Vault → point to your synced wiki/ folder
```

Once configured, ChiefOS syncs `wiki/` and `raw/` to the cloud every 15 minutes via cron.
The agent writes on the server; you read and explore in Obsidian on your local machine.

**Obsidian tips:**
- Enable the **Graph View** (left sidebar) to visualize how pages link to each other
- Install the **Dataview** plugin to query wiki pages by frontmatter tags
- Install **Obsidian Web Clipper** (browser extension) to clip articles directly to `raw/`

---

## Twilio (Optional)

Only required if you want to use `make-call.sh` for phone call alerts.

| Variable | Required | Example | Description |
|---|---|---|---|
| `TWILIO_ACCOUNT_SID` | — | `ACxxxxx` | Twilio Account SID from your Twilio console. |
| `TWILIO_AUTH_TOKEN` | — | `xxxxxxxx` | Twilio Auth Token. |
| `TWILIO_FROM_NUMBER` | — | `+15550001234` | Your Twilio phone number (must be verified). |

---

## Complete Example

```bash
# ============================================================
# config.env — ChiefOS Configuration
# ============================================================

# Core
BASE_DIR=/home/chiefos/chiefos
COS_USER=chiefos
BASE_URL=hq.yourdomain.com
DB_NAME=chiefos.db
TZ=America/New_York

# Email
GMAIL_USER=you@gmail.com
GMAIL_PASS=abcd efgh ijkl mnop
OWNER_EMAIL=you@yourdomain.com

# Alerting
ALERT_SCRIPT=$BASE_DIR/scripts/utils/send_alert.sh
TELEGRAM_TOKEN=1234567890:AABBCCDDEEFFaabbccdd
TELEGRAM_CHAT_ID=987654321

# Angel
ANGEL_PORT=39571
ANGEL_REPO=https://github.com/your/angel-repo
ANGEL_MODEL=google
ANGEL_API_KEY=AIzaSyYourKeyHere
```

---

## After Changing Config

If you change `config.env` after installation:

```bash
# Re-apply config to deployed scripts
find $BASE_DIR/scripts -type f \( -name "*.py" -o -name "*.sh" \) -exec \
  sed -i "s|OLD_BASE_DIR|$BASE_DIR|g; s|OLD_DB_NAME|$DB_NAME|g" {} \;

# Update the deployed .env
cp config.env $BASE_DIR/.env
chmod 600 $BASE_DIR/.env

# Restart Angel if her port changed
sudo -u angel pm2 restart angel
```
