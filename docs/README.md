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
- **Wiki knowledge base** — a persistent, compounding knowledge base your agent maintains. Drop files into `raw/`, ask your agent to ingest them. Knowledge accumulates and cross-references over time rather than being re-derived on every query

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
        ├── www/HQ/          ← 10 live dashboards
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
| Schedule | `/HQ/schedule/` | Todos and events; travel shows location + notes |
| Content | `/HQ/posts/` | Social posts and content pipeline |
| Projects | `/HQ/projects/` | Active projects, tasks, overdue tracking |
| Comms | `/HQ/comms/` | Contacts directory with star ratings |
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

## Wiki Knowledge Base + Obsidian

ChiefOS includes a persistent, compounding knowledge base your agent maintains over time.

```
$BASE_DIR/
├── wiki/       ← agent-maintained pages (cross-linked markdown)
└── raw/        ← drop source files here for ingestion
```

**How it works:**
1. Drop any file (article, report, transcript, notes) into `raw/`
2. Tell your agent: *"Ingest raw/filename.md into the wiki"*
3. The agent reads it, writes wiki pages, updates cross-links and the index
4. Knowledge compounds — every ingest makes the whole wiki richer

**Visualization via Obsidian:**
Point [Obsidian](https://obsidian.md/) at your synced `wiki/` folder to get a full graph view of how all your knowledge connects. Enable **rclone sync** in `config.env` to keep it in sync automatically.

```
Agent writes → server wiki/ → rclone → cloud storage → Obsidian (your device)
```

**Wiki tools:**
```bash
bash scripts/wiki/ingest_prep.sh <filename>    # preview + log a source
bash scripts/wiki/search_wiki.sh <query>       # search all pages
bash scripts/wiki/lint_wiki.sh                 # audit health
bash scripts/wiki/sync_wiki.sh                 # manual sync to cloud
```

Already have ChiefOS or OpenClaw installed? Add the wiki with one command:
```bash
bash wiki-install.sh
```

---

## Existing OpenClaw Users

If you have an existing OpenClaw workspace, the installer detects it and runs `openclaw/patch_openclaw.sh` instead of a fresh install. Your agent identity is preserved — ChiefOS only adds the governance layer and schema.

---

## License

MIT — see `LICENSE`.
