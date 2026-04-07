# ChiefOS

**A self-hosted AI Chief of Staff backend. Plug in your own AI. Own your data.**

ChiefOS gives your AI agent a complete operational backbone: a structured SQLite database, real-time dashboards, scheduled alerts, email monitoring, and a governance layer — all running on your own server.

<!-- [Screenshot: HQ Briefing Dashboard] -->

---

## What It Does

- **10 HQ dashboards** — Briefing, Finance, Property, Schedule, Content, Projects, Security, Knowledge, and more — all fed from a local SQLite database
- **8 scheduled alerts** — daily bills, deposits, maintenance, email digest, todos, weekly preview, project status, monthly summary — all delivered to Telegram
- **25-table schema** — structured data across every life and business domain: properties, projects, tasks, contacts, finance, subscriptions, events, and more
- **Guardian (Angel)** — an independent governance layer running as a separate OS user that authorizes consequential agent actions before they execute
- **Model-agnostic** — works with any AI that can read files and run shell commands (Claude, GPT-4, Gemini, local models)
- **One-command install** — `bash install.sh` walks you through everything

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR/CHIEFOS.git
cd CHIEFOS

# 2. Copy and fill in your configuration
cp config.env.template config.env
nano config.env

# 3. Run the installer
bash install.sh
```

That's it. The installer handles users, directories, database, dashboards, Angel, Nginx, and crontab. Takes 5–10 minutes. See `docs/SETUP.md` for a full walkthrough including a prerequisite checklist.

---

## Requirements

| Requirement | Version |
|---|---|
| OS | Ubuntu 20.04+ / Debian 11+ |
| Python | 3.8+ |
| SQLite | Any |
| Node.js | 18+ |
| npm | 8+ |
| Git | Any |
| PM2 | Any (auto-installed if missing) |
| curl | Any |
| sudo access | Required (Angel runs as a separate user) |
| Disk space | 500MB minimum |

---

## Architecture

```
Your AI Agent (any model)
        │
        ├── Reads: SOUL.md, TOOLS.md, AGENTS.md
        ├── Queries: chiefos.db (SQLite, 27 tables)
        ├── Runs: scripts/ (Python + Bash)
        │
        ▼
    ChiefOS HQ
        ├── www/HQ/          ← 8 live dashboards
        ├── scripts/core/    ← hydrators, add_todo.py
        ├── scripts/alerts/  ← 8 scheduled alert scripts
        └── scripts/utils/   ← email, security, monitoring

        ▼
    Angel (Governance)
        └── Separate OS user, MCP server
            Authorizes all consequential actions
```

---

## HQ Dashboards

| Domain | URL | What It Shows |
|---|---|---|
| Briefing | `/HQ/briefing/` | Daily intelligence brief |
| Finance | `/HQ/finance/` | Transactions, bills, subscriptions |
| Property | `/HQ/property/` | Asset status, maintenance, cleaning |
| Schedule | `/HQ/schedule/` | Todos and events calendar |
| Content | `/HQ/posts/` | Social posts and content pipeline |
| Security | `/HQ/security/` | Network events and perimeter logs |
| Weekly | `/HQ/weekly_layout/` | Weekly rhythm visualization |

---

## Configuration

All configuration lives in `config.env`. Copy `config.env.template` to get started.

Key variables:

| Variable | Purpose |
|---|---|
| `BASE_DIR` | ChiefOS workspace root path |
| `COS_USER` | OS user running ChiefOS |
| `BASE_URL` | Your domain (no `http://`) |
| `TELEGRAM_TOKEN` | Bot token for alerts |
| `TELEGRAM_CHAT_ID` | Your Telegram user ID |
| `GMAIL_USER` | Email address to monitor |
| `ANGEL_REPO` | Angel governance service repo |

See `docs/CONFIGURATION.md` for every variable.

---

## Existing OpenClaw Users

If you have an existing OpenClaw workspace, the installer detects it and runs `openclaw/patch_openclaw.sh` instead of a fresh install. Your agent identity is preserved — ChiefOS only adds the governance layer and schema.

---

## License

MIT — see `LICENSE`.
