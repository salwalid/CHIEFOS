<p align="center">
  <span style="font-size:3rem;">🏛️</span>
</p>

<h1 align="center">CHIEFOS</h1>

<p align="center">
  <strong>A self-hosted AI Chief of Staff backend.</strong><br>
  Plug in your own AI. Own your data. Run your ops.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#what-it-does">What It Does</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#hq-dashboards">Dashboards</a> ·
  <a href="#ecosystem">Ecosystem</a> ·
  <a href="https://github.com/salwalid/CHIEFOS/issues">Issues</a>
</p>

---

## The Problem

AI agents are powerful — but they run in sandboxes, lose context between sessions, and have no structured memory of *your* life. They can write code and answer questions, but they can't track your bills, monitor your inbox, brief you on your day, or manage your projects — not without a backend built for it.

CHIEFOS is that backend.

---

## What It Does

CHIEFOS gives your AI agent a **complete operational backbone**: a structured database, real-time dashboards, scheduled alerts, email monitoring, a compounding knowledge base, and a governance layer — all running on your own server, with your own models.

| Capability | Details |
|---|---|
| **10 HQ Dashboards** | Briefing, Finance, Property, Schedule, Content, Projects, Comms, Security, Knowledge, Weekly Rhythm |
| **8 Scheduled Alerts** | Bills, deposits, maintenance, email digest, todos, weekly preview, project status, monthly summary — all via Telegram |
| **25-Table Schema** | Structured data across every life and business domain: properties, projects, tasks, contacts, finance, subscriptions, events |
| **Wiki Knowledge Base** | Persistent, compounding knowledge your agent maintains over time. Drop files in, agent ingests them. Syncs to Obsidian |
| **Outbound Voice** | Twilio-powered voice calls for critical alerts when Telegram isn't enough |
| **Email Monitoring** | Gmail integration — surfaces important emails, filters noise |
| **Security Perimeter** | Fail2Ban monitoring, login reports, network event tracking |
| **Model-Agnostic** | Works with any AI that can read files and run shell commands — Claude, GPT, Gemini, local models |
| **One-Command Install** | `bash install.sh` handles everything: users, directories, database, dashboards, governance, Nginx, crontab |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/salwalid/CHIEFOS.git
cd CHIEFOS

# 2. Configure
cp config.env.template config.env
nano config.env                    # fill in your values

# 3. Install
bash install.sh                    # 5–10 minutes, fully guided
```

The installer walks you through everything: OS user creation, database schema, dashboard deployment, governance layer, Nginx reverse proxy, and crontab scheduling. See `docs/SETUP.md` for the full walkthrough.

### Requirements

| Requirement | Version |
|---|---|
| OS | Ubuntu 20.04+ / Debian 11+ |
| Python | 3.8+ |
| SQLite | Any |
| Node.js | 18+ |
| sudo | Required (governance runs as a separate OS user) |
| Disk | 500MB minimum |

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│  YOU                                             │
│  ├── CLI / Chat / API                            │
│  └── Any AI agent (Claude, GPT, Gemini, local)   │
└──────────────────┬───────────────────────────────┘
                   │
                   │  reads SOUL.md, TOOLS.md, AGENTS.md
                   │  queries chiefos.db (SQLite, 25 tables)
                   │  runs scripts/ (Python + Bash)
                   │
┌──────────────────▼───────────────────────────────┐
│  CHIEFOS CORE                                    │
│  ├── scripts/core/     hydrators, task mgmt      │
│  ├── scripts/alerts/   8 scheduled alert scripts │
│  ├── scripts/utils/    email, security, voice    │
│  ├── scripts/wiki/     knowledge base tools      │
│  └── www/HQ/           10 live dashboards        │
└──────────────────┬───────────────────────────────┘
                   │
                   │  every consequential action
                   │  requires authorization
                   │
┌──────────────────▼───────────────────────────────┐
│  GOVERNANCE (MaatSpec)                           │
│  ├── Separate OS user (process isolation)        │
│  ├── MCP server on dedicated port                │
│  ├── 5-tier risk classification                  │
│  └── Authorizes before execution                 │
└──────────────────────────────────────────────────┘
```

**Key design decisions:**

- **SQLite, not Postgres** — zero ops, single-file backup, survives anything. Your entire life in one `.db` file you can `scp` anywhere.
- **Separate governance user** — the agent cannot bypass its own guardrails because the guardrails run as a different OS user with different permissions.
- **File-based agent interface** — `SOUL.md` defines identity, `TOOLS.md` defines capabilities, `AGENTS.md` defines delegation rules. Any AI that can read markdown can pilot CHIEFOS.
- **Hydration pattern** — Python scripts pull from the database and write JSON files that dashboards consume. No frontend framework. No build step. Just HTML that reads JSON.

---

## HQ Dashboards

Ten dashboards served via Nginx, all hydrated from your local SQLite database:

| Dashboard | Path | Purpose |
|---|---|---|
| **Briefing** | `/HQ/briefing/` | Daily intelligence brief — your morning scroll |
| **Finance** | `/HQ/finance/` | Transactions, upcoming bills, subscriptions |
| **Property** | `/HQ/property/` | Asset status, maintenance schedules, cleaning |
| **Schedule** | `/HQ/schedule/` | Todos, events, travel with location + notes |
| **Content** | `/HQ/posts/` | Social posts and content pipeline |
| **Projects** | `/HQ/projects/` | Active projects, tasks, overdue tracking |
| **Comms** | `/HQ/comms/` | Contacts directory with star ratings |
| **Security** | `/HQ/security/` | Network events, Fail2Ban, perimeter logs |
| **Weekly** | `/HQ/weekly_layout/` | Weekly rhythm visualization |
| **Mission Control** | `/HQ/mission-control/` | High-level operational overview |

---

## Alerts

Eight scheduled scripts deliver Telegram notifications at the right time:

| Alert | Trigger | What It Does |
|---|---|---|
| `todo_alert.py` | Morning | Today's tasks + overdue + horizon (configurable lookahead) |
| `lead_up_checks.py` | Morning | Targeted pings for approaching high-priority deadlines |
| `bill_reminder.py` | Daily | Upcoming bills within reminder window |
| `deposit_reminder.py` | Daily | Expected incoming deposits |
| `maintenance_tracker.py` | Daily | Property maintenance due dates |
| `morning_email_review.py` | Morning | Gmail digest — important emails surfaced |
| `weekly_preview.py` | Sunday | Week-ahead briefing |
| `monthly_summary.py` | 1st of month | Month-in-review across all domains |

All alert thresholds are tunable via `config.env` — horizon days, overdue caps, lead-up timing, priority filters.

---

## Wiki Knowledge Base

A persistent, compounding knowledge base your agent maintains over time — not a vector database that forgets context, but structured markdown that accumulates and cross-references.

```
$CHIEFOS_HOME/
├── wiki/       ← agent-maintained pages (cross-linked markdown)
└── raw/        ← drop source files here for ingestion
```

**How it works:**

1. Drop any file into `raw/` — articles, reports, transcripts, notes
2. Tell your agent: *"Ingest raw/filename.md into the wiki"*
3. Agent reads it, writes wiki pages, updates cross-links and the index
4. Knowledge compounds — every ingest makes the whole wiki richer

**Obsidian integration:** Sync your `wiki/` folder to any cloud storage via rclone, then open it as an Obsidian vault. Full graph view of how all your knowledge connects.

```bash
# Wiki tools
bash scripts/wiki/search_wiki.sh <query>       # search all pages
bash scripts/wiki/lint_wiki.sh                 # audit health
bash scripts/wiki/sync_wiki.sh                 # manual sync to cloud
bash scripts/wiki/ingest_prep.sh <filename>    # preview a source before ingesting
```

---

## Configuration

All configuration lives in `config.env` (copy from `config.env.template`):

```bash
# Core
BASE_DIR=/home/youruser/chiefos      # where CHIEFOS lives
COS_USER=youruser                    # OS user running it
BASE_URL=yourdomain.com              # your domain or IP
TZ=America/New_York                  # your timezone

# Alerts (Telegram)
TELEGRAM_TOKEN=your_bot_token        # @BotFather → /newbot
TELEGRAM_CHAT_ID=your_chat_id        # @userinfobot → your ID

# Governance
ANGEL_PORT=39571                     # governance MCP server port
ANGEL_MODEL=google                   # google | anthropic | openai

# Optional
GMAIL_USER=your@gmail.com            # email monitoring
RCLONE_REMOTE=gdrive                 # wiki cloud sync
TWILIO_ACCOUNT_SID=...               # voice call alerts
```

See `docs/CONFIGURATION.md` for every variable and what it controls.

---

## Ecosystem

CHIEFOS is the backbone. These projects extend it:

<table>
  <tr>
    <td align="center" width="50%">
      <a href="https://github.com/salwalid/Entrovergence">
        <strong>⚖️ Entrovergence</strong>
      </a>
      <br><br>
      A multi-model deliberation council. Four AI panelists debate and peer-review before a single answer leaves the chamber. Plugs into CHIEFOS as a skill.
      <br><br>
      <code>Entropy meets convergence.</code>
    </td>
    <td align="center" width="50%">
      <a href="https://maatspec.org">
        <strong>🪶 MaatSpec</strong>
      </a>
      <br><br>
      The governance framework. 5 risk tiers, 4 enforcement layers. Powers CHIEFOS's authorization system. Named after Ma'at — the Egyptian goddess of truth and cosmic order.
      <br><br>
      <code>Autonomy without anarchy.</code>
    </td>
  </tr>
</table>

---

## Philosophy

CHIEFOS exists because of a few strong opinions:

1. **Your AI should know your life** — not just answer generic questions, but understand your projects, finances, schedule, contacts, and priorities in a structured way that compounds over time.

2. **Self-hosting is not optional** — if your AI assistant knows everything about you, that data should live on hardware you control. Period.

3. **Governance is structural, not behavioral** — telling an AI "don't do bad things" is not governance. Running the guardrails as a separate process with separate permissions is.

4. **Model-agnostic by design** — the best model today won't be the best model tomorrow. CHIEFOS doesn't care which brain it's connected to. Swap providers with a config change.

5. **Files over APIs** — `SOUL.md` is more portable than a proprietary agent config. Any AI that reads markdown can pilot CHIEFOS. That's the point.

---

## License

MIT — see [LICENSE](LICENSE)

---

<p align="center">
  <sub>Built by a human who ships. <a href="https://phatfaro.com">phatfaro.com</a></sub>
</p>
