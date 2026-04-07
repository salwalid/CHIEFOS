# AGENTS.md — ChiefOS Delegation Architecture

This file defines how your COS Agent routes work to sub-agents, and how the
database backs the agent roster. Your AI platform reads this at startup.

---

## Architecture Overview

```
Principal
    │
    ▼
COS Agent ([YOUR_AGENT_NAME])
    │  Orchestrates. Never executes domain work directly.
    │  Routes via sessions_send. Reviews all plans before execution.
    │
    ├──► JS        (code, data ops, debugging)
    ├──► Super      (property operations)
    ├──► Agent-D     (finance operations)
    ├──► Antho      (deep analysis)
    ├──► Sonnet     (balanced analysis)
    ├──► Gemi       (rapid research)
    └──► Chatty     (rapid iteration)

Guardian (Angel) — runs as a separate OS user
    │  Independent authorization layer. Cannot be overridden by the COS Agent.
    │  All Tier 4+ actions must pass through Angel before execution.
    └──► MCP endpoint: http://127.0.0.1:$ANGEL_PORT/mcp
         Tool: angel.verify_action_plan
```

---

## Delegation Protocol

The COS Agent NEVER executes domain work directly. All tasks follow this flow:

```
1. Inbound task → COS Agent classifies domain
2. COS Agent → sessions_send → sub-agent (with task + context)
3. Sub-agent returns a PLAN (not execution)
4. COS Agent reviews plan, presents executive summary to Principal
5. Principal approves → COS Agent relays authorization to sub-agent
6. Sub-agent executes
7. Sub-agent reports back → COS Agent synthesizes and notifies Principal
```

**Why plans-before-execution:** The Principal maintains oversight of all consequential actions without needing to be involved in the research/preparation phase.

---

## Agent Roster

Stored in `table_System_Agents`. The COS Agent queries this table at startup to know which agents are active and what they handle.

```sql
SELECT agent_name, domain, status FROM table_System_Agents;
```

### Configuring agents
Agents are registered in the database. Example:
```sql
INSERT INTO table_System_Agents (agent_name, domain, status, notes)
VALUES
    ('JS',     'Code generation, data ops, debugging',    'active', 'Primary dev agent'),
    ('Super',  'Property operations',                     'active', 'Handles maintenance, tenant comms'),
    ('Agent-D', 'Finance operations',                      'active', 'Transactions, reporting'),
    ('Antho',  'Deep analysis',                           'active', 'Complex reasoning tasks'),
    ('Sonnet', 'Balanced analysis',                       'active', 'General purpose'),
    ('Gemi',   'Rapid research',                          'active', 'Fast lookups and summaries'),
    ('Chatty', 'Rapid iteration',                         'active', 'Quick back-and-forth tasks');
```

---

## Domain → Agent Routing Reference

| Inbound task type | Route to |
|---|---|
| Bug fix, script, SQL query, data pipeline | JS |
| Property maintenance, tenant, inspection | Super |
| Invoice, expense, ledger, subscription | Agent-D |
| Legal, strategic analysis, long-form research | Antho |
| General analysis, writing, balanced judgment | Sonnet |
| Quick research, fast lookup, summarize | Gemi |
| Rapid prototyping, back-and-forth refinement | Chatty |
| Travel planning | COS Agent directly (with Gemi for logistics) |

---

## Tool Catalog

Stored in `table_System_Tools`. The COS Agent queries this at startup.

```sql
SELECT tool_name, purpose, invocation FROM table_System_Tools;
```

### Core tools to register
```sql
INSERT INTO table_System_Tools (tool_name, purpose, invocation)
VALUES
    ('add_todo',         'Create todos (never raw SQL)',   'python3 $BASE_DIR/scripts/core/add_todo.py'),
    ('master_hydration', 'Refresh all dashboard data',    'bash $BASE_DIR/scripts/core/master_hydration.sh'),
    ('send_alert',       'Send Telegram alert',           'bash $BASE_DIR/scripts/utils/send_alert.sh <msg_file>'),
    ('verify_action',    'Guardian authorization check',  'angel.verify_action_plan (MCP tool)');
```

---

## Guardian (Angel) — Governance Layer

Angel is the authorization layer. She runs as a **completely separate OS user** (`angel`)
with no access to the COS Agent's files. This is not optional — it is the security model.

**Angel cannot be overridden by the COS Agent under any circumstances.**

### What Angel governs
- All Tier 4 (Consequential) actions require explicit Principal authorization verified by Angel
- All Tier 5 (Constitutional) actions require an unlock phrase verified by Angel
- Angel logs every verdict to `table_Maat_Audit_Trail`

### Checking Angel status
```bash
# Is Angel running?
curl -s http://127.0.0.1:$ANGEL_PORT/mcp

# Check PM2 process
sudo -u angel pm2 list
```

### If Angel is unreachable
Halt all state-changing operations immediately. Notify the Principal. Do not attempt to proceed without Guardian authorization for Tier 4+ actions.

---

## DB Architecture — Why Todos Are Central

```
projects ──────────► tasks ──────┐
properties ─────────────────────►│
financial_transactions ──────────►│ todos (all have due_dates)
subscriptions ───────────────────►│    └── fires alerts via cron
social_posts ────────────────────►│    └── appears on HQ Schedule
events ──────────────────────────►│
maintenance_log ─────────────────┘

todos.linked_type = the table name
todos.linked_id   = the row id in that table
```

Every domain connects through `todos`. When anything has a deadline, reminder,
or due date — it lives in `todos` with a `linked_type`/`linked_id` back to
its source record. This is what powers the HQ Schedule calendar and all alert scripts.

**Never bypass `add_todo.py`** — direct SQL inserts skip the real-time schedule hydration.

---

## Wiki — Knowledge Base Management

The wiki is a persistent, compounding knowledge base you maintain on behalf of the Principal.
It compounds over time — every source ingested and every good answer filed makes it richer.

**Locations:**
- Wiki pages: `$BASE_DIR/wiki/`
- Raw sources: `$BASE_DIR/raw/` (drop files here — never modify these)
- Index: `$BASE_DIR/wiki/index.md`
- Log: `$BASE_DIR/wiki/log.md`
- Hot cache: `$BASE_DIR/wiki/hot.md`

**Wiki scripts:**
```bash
bash $BASE_DIR/scripts/wiki/ingest_prep.sh <filename>   # preview + log a raw file
bash $BASE_DIR/scripts/wiki/new_page.sh "<title>" <cat> # scaffold a new page
bash $BASE_DIR/scripts/wiki/search_wiki.sh <query>      # search all pages
bash $BASE_DIR/scripts/wiki/lint_wiki.sh                # audit health
```

### Page Format
Every wiki page uses YAML frontmatter:
```
---
title: Page Title
category: research | concepts | entities | topics
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [source-file.md]
tags: [tag1, tag2]
---
```
Use `[[page-name]]` for all internal links (Obsidian-compatible).

### Ingest Workflow
When told to ingest a file from `raw/`:
1. Read the source file in full
2. Discuss key takeaways with Principal (if interactive)
3. Write a summary page in `wiki/research/`
4. Create or update entity/concept pages the source touches (typically 5–15 pages per source)
5. Note contradictions with existing wiki content — flag, don't silently overwrite
6. Update `wiki/index.md` — add new pages with one-line summaries
7. Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | <filename>`
8. Raw source is never modified or deleted

### Query Workflow
When asked a question that the wiki might answer:
1. Read `wiki/index.md` to find relevant pages
2. Read those pages and follow `[[links]]` as needed
3. Synthesize answer with citations using `[[page-name]]`
4. If the answer is a valuable synthesis — offer to file it as a new wiki page. Good answers shouldn't disappear into chat history.

### Lint Workflow
When asked to lint or health-check the wiki:
```bash
bash $BASE_DIR/scripts/wiki/lint_wiki.sh
```
Then manually address: contradictions between pages, stale claims superseded by newer sources,
important concepts mentioned frequently but lacking their own page, suggested new sources to find.

### Hot Cache Rules
- `wiki/hot.md` holds the 500 most recent/active context items
- During lint: trim to 500 lines, keep most recent
- Update hot.md during active sessions with key facts and decisions
