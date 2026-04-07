# TOOLS.md — ChiefOS Agent Reference
**Schema version: 1.0 — 27 tables**

---

## RULE #1 — Creating Todos (ALWAYS use the wrapper — never raw SQL)

When the Principal asks you to remember, remind, or track anything — use `add_todo.py`.
This inserts into the `todos` table AND immediately updates the HQ Schedule page.
The item will appear on the calendar within 60 seconds — no manual refresh needed.

```bash
python3 $BASE_DIR/scripts/core/add_todo.py \
    --title "Call plumber re: leaking tap" \
    --category property \
    --priority high \
    --due_date 2026-04-05 \
    --reminder_date 2026-04-04 \
    --linked_type properties \
    --linked_id PROP_ID_HERE \
    --notes "Details about the job"
```

**Never insert into `todos` directly with raw SQL** — the schedule won't update.

---

## Database

- **Path:** `$BASE_DIR/$DB_NAME` (SQLite)
- **Role:** Single source of truth for all operational data
- **Dead tables — DO NOT USE:** Any table not listed below. If you encounter an old name, it has been migrated — query the new schema only.

---

## Schema Reference

### todos
The backbone — every reminder, deadline, and due-date item across all domains.
**Always use `add_todo.py` to insert. Never raw SQL.**

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | INTEGER | Auto PK |
| title | TEXT | Short description of the action |
| category | TEXT | `project` / `finance` / `property` / `content` / `personal` |
| linked_type | TEXT | `projects` / `tasks` / `social_posts` / `properties` / `financial_transactions` / `subscriptions` / NULL |
| linked_id | INTEGER | ID of the linked row in the linked_type table |
| priority | TEXT | `high` / `medium` / `low` |
| status | TEXT | `open` / `in_progress` / `done` / `snoozed` |
| due_date | TEXT | ISO date: `YYYY-MM-DD` — shows on HQ Schedule calendar |
| reminder_date | TEXT | ISO date: `YYYY-MM-DD` — fires alert on this date |
| notes | TEXT | Any extra context |
| created_at | TEXT | Auto-set to datetime('now') |

---

### tasks
Work items inside a project. Linked to `projects` via `project_id`.

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | INTEGER | Auto PK |
| project_id | INTEGER | FK → projects.id — **required** |
| title | TEXT | Task name |
| status | TEXT | `open` / `in_progress` / `done` / `blocked` |
| priority | TEXT | `high` / `medium` / `low` |
| assigned_to | TEXT | Agent name or "Principal" |
| notes | TEXT | Details |
| created_at | TEXT | Auto-set |

**Note:** A task needs a linked `todo` with a `due_date` to appear on the HQ Schedule calendar.

---

### projects
Active and archived initiatives.

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | INTEGER | Auto PK |
| name | TEXT | Project name |
| description | TEXT | What this project is |
| status | TEXT | `active` / `on_hold` / `completed` / `cancelled` |
| priority | TEXT | `high` / `medium` / `low` |
| owner | TEXT | Typically "Principal" |
| due_date | TEXT | ISO date: `YYYY-MM-DD` |
| notes | TEXT | Current status, blockers, context |
| created_at | TEXT | Auto-set |

---

### financial_transactions
Income and expenses across all properties and categories.

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | INTEGER | Auto PK |
| date | TEXT | ISO date: `YYYY-MM-DD` |
| amount | REAL | Positive = income, negative = expense |
| type | TEXT | `income` / `expense` |
| category | TEXT | `rent` / `mortgage` / `repair` / `tax` / `insurance` / `utilities` / `personal` / `other` |
| property_id | TEXT | FK → properties.id — NULL if not property-related |
| description | TEXT | What this transaction is |
| notes | TEXT | Extra context |

**Example — record rent received:**
```sql
INSERT INTO financial_transactions (date, amount, type, category, property_id, description)
VALUES ('2026-04-01', 2400.00, 'income', 'rent', 'PROP_ID', 'April rent — 123 Main St');
```

---

### subscriptions
Recurring bills and services.

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | INTEGER | Auto PK |
| name | TEXT | Service name (e.g. "GitHub Pro", "Adobe CC") |
| amount | REAL | Recurring charge amount |
| frequency | TEXT | `monthly` / `annual` / `quarterly` |
| category | TEXT | `software` / `hosting` / `media` / `utilities` / `other` |
| next_due_date | TEXT | ISO date: `YYYY-MM-DD` — when next charge hits |
| status | TEXT | `active` / `cancelled` / `paused` |
| notes | TEXT | Account details, login hints, cancellation notes |

---

### events
Travel, meetings, important dates, and deadlines with a time component.

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | INTEGER | Auto PK |
| title | TEXT | Event name |
| type | TEXT | `travel` / `meeting` / `deadline` / `personal` / `property` |
| start_datetime | TEXT | ISO datetime: `YYYY-MM-DD HH:MM` or date only |
| end_datetime | TEXT | ISO datetime — can be NULL for single-day events |
| location | TEXT | City, address, or "remote" |
| project_id | INTEGER | FK → projects.id — optional |
| notes | TEXT | Details, booking refs, contacts |

---

### maintenance_log
Property maintenance jobs — scheduled, in progress, or completed.

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | INTEGER | Auto PK |
| property_id | INTEGER | FK → properties.id |
| contact_id | INTEGER | FK → contacts.id — NULL if not yet assigned |
| work_type | TEXT | `plumbing` / `electrical` / `hvac` / `landscaping` / `cleaning` / `inspection` / `repair` / `other` |
| description | TEXT | What needs to be done or was done |
| status | TEXT | `open` / `scheduled` / `in_progress` / `completed` / `cancelled` |
| scheduled_date | TEXT | ISO date: `YYYY-MM-DD` |
| completed_date | TEXT | ISO date — fill when done |
| cost | REAL | Actual cost when known |
| notes | TEXT | Contractor notes, access instructions, follow-up |

---

### properties
All real estate assets.

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | TEXT | Primary key — text identifier (e.g. property name or short code) |
| name | TEXT | Full property name or address |
| type | TEXT | `residential` / `commercial` / `land` / `short_term_rental` |
| status | TEXT | `occupied` / `vacant` / `under_maintenance` / `listed` |
| cleaning_status | TEXT | `clean` / `needs_cleaning` / `scheduled` |
| last_maintenance | TEXT | ISO date of last maintenance |
| next_tax_due | TEXT | ISO date of next property tax due |
| critical_notes | TEXT | Anything the Agent must always know about this property |

---

### contacts
Contractors, vendors, and tenants.

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | INTEGER | Auto PK |
| name | TEXT | Full name or company name |
| specialty | TEXT | `plumber` / `electrician` / `cleaner` / `tenant` / `lawyer` / `accountant` / `vendor` / `other` |
| contact_info | TEXT | Phone, email, or both |
| last_used | TEXT | ISO date last engaged |
| rating | INTEGER | 1–5 — your rating of this contact |

---

### property_utilities
Utility accounts linked to properties.

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | INTEGER | Auto PK |
| asset_id | INTEGER | FK → properties.id |
| vendor | TEXT | Utility company name |
| account_number | TEXT | Account number with the vendor |
| contact_info | TEXT | Vendor phone or website |
| notes | TEXT | Auto-pay status, login info hints, notes |

---

### context_vault
Strategic concepts, breakthroughs, and domain knowledge worth preserving.

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | INTEGER | Auto PK |
| domain | TEXT | `finance` / `property` / `projects` / `security` / `personal` / `system` |
| concept | TEXT | Short name of the concept or insight |
| breakthrough | TEXT | The actual insight or learning |
| implementation_link | TEXT | URL or file path if applicable |
| horizon | TEXT | `immediate` / `short` / `long` / `permanent` |
| principal_sentiment | TEXT | `positive` / `neutral` / `concern` |
| timestamp | TEXT | Auto-set |
| related_mission_id | INTEGER | Optional link to a project |
| tags | TEXT | Comma-separated keywords |

---

### chronicles
Lessons learned — failures, successes, incidents worth remembering.

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | INTEGER | Auto PK |
| timestamp | TEXT | When it happened |
| component | TEXT | System or domain affected (e.g. "hydration", "finance", "property") |
| event | TEXT | What happened |
| error_log | TEXT | Raw error or output if applicable |
| lesson_learned | TEXT | What to do differently next time |
| context_id | INTEGER | Optional FK to context_vault |
| session_date | TEXT | ISO date of the session |

---

### social_posts
Content posts (LinkedIn, blog, other platforms).
**DO NOT rename this table** — the briefing engine depends on it.

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | TEXT | Primary key — post identifier |
| title | TEXT | Post title or headline |
| platform | TEXT | `linkedin` / `blog` / `instagram` / `other` |
| status | TEXT | `DRAFT` / `SCHEDULED` / `PUBLISHED` / `ARCHIVED` |
| post_date | TEXT | ISO date scheduled or published |

---

### security_events
Network and perimeter events logged by the security monitor.
**Read-only — do not insert manually.**

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | INTEGER | Auto PK |
| timestamp | TEXT | When the event occurred |
| event_type | TEXT | Type of security event |
| ip_address | TEXT | Source IP |
| isp | TEXT | ISP name if resolved |
| status | TEXT | `flagged` / `reviewed` / `blocked` / `ok` |

---

### table_principle_week_blueprint
The static reference matrix for the Principal's ideal weekly rhythm. Use for "Life Design" enforcement and scheduling awareness.

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | INTEGER | Auto PK |
| day_of_week | TEXT | `Monday` through `Sunday` |
| start_time | TEXT | 24h format: `HH:MM` |
| end_time | TEXT | 24h format: `HH:MM` |
| activity_name | TEXT | Name of the ritual or block |
| focus_type | TEXT | `High Focus` / `Health` / `Creative` / `Rest` / etc. |
| alpha_protocol | TEXT | Internal instruction for Agent behavior |
| notes | TEXT | Any extra context or the "Why" |
| created_at | DATETIME | Auto-set |

---

### routines
Recurring task sequences and protocols.

| Column | Type | Valid Values / Notes |
|---|---|---|
| id | INTEGER | Auto PK |
| routine_name | TEXT | Name of the routine |
| sequence_id | INTEGER | Order within the routine |
| component_name | TEXT | Which system or script this step involves |
| action_requirement | TEXT | What needs to happen |
| time_window | TEXT | When this step should run |
| status | TEXT | `active` / `paused` / `retired` |
| principal_note | TEXT | Special instructions from the Principal |

---

## System Tables — READ ONLY, NEVER MODIFY STRUCTURE

| Table | Purpose |
|---|---|
| `table_Alpha_Intel` | Key/value store — critical runtime config. Read with `SELECT value FROM table_Alpha_Intel WHERE key='...'` |
| `table_Maat_Audit_Trail` | Every tiered action and Guardian verdict — append only |
| `table_Memory_Index` | Keyword-to-table lookup index |
| `table_System_Agents` | Agent roster |
| `table_System_Tools` | Tool catalog |
| `table_Usage_Ledger` | Token consumption per session |
| `table_Latency_Tests` | Diagnostic benchmarks |
| `agent_state_history` | Sub-agent status log |
| `system_environment` | Global runtime config |

---

## HQ Dashboard Pages

| Domain | Page URL | Hydrated by |
|---|---|---|
| 1 — Briefing | `/HQ/briefing/` | `daily_briefing_v11.py` + `hq_briefing_hydrator_v6.py` |
| 2 — Finance | `/HQ/finance/` | `hydrate_finance.py` |
| 3 — Property | `/HQ/property/` | `hydrate_properties.py` |
| 4 — Schedule | `/HQ/schedule/` | `hydrate_schedule.py` |
| 5 — Content | `/HQ/posts/` | `hydrate_content.py` |
| 6 — Projects | `/HQ/projects/` | `hydrate_projects.py` |
| 7 — Comms | `/HQ/comms/` | *(future)* |
| 8 — Security | `/HQ/security/` | `hydrate_security.py` |
| 9 — Knowledge | `/HQ/vault/` | `hydrate_vault.py` |
| 10 — Weekly | `/HQ/weekly_layout/` | `hydrate_weekly_layout.py` |

All hydrators write JSON to `$BASE_DIR/www/HQ/<domain>/`. Dashboards auto-refresh every 60 seconds.

Run all hydrators in sequence:
```bash
bash $BASE_DIR/scripts/core/master_hydration.sh
```

---

## Alert Scripts (run via cron)

| Script | Schedule (your TZ) | Purpose |
|---|---|---|
| `bill_reminder.py` | 5:00am daily | Bills and subscriptions due within 14 days |
| `deposit_reminder.py` | 5:00am daily | Expected deposits not yet received |
| `maintenance_tracker.py` | 5:00am daily | Open maintenance jobs |
| `morning_email_review.py` | 5:00am daily | Overnight email digest |
| `todo_alert.py` | 5:30am daily | Todos due today or overdue |
| `weekly_preview.py` | 5:45am daily + Sunday 8pm | Week ahead summary |
| `project_status.py` | Monday 9:00am | Active project status |
| `monthly_summary.py` | Last day of month 9pm | Monthly finance and activity summary |

All alert scripts send via `$BASE_DIR/scripts/utils/send_alert.sh` (Telegram by default).

---

## Wiki Knowledge Base

A persistent, compounding knowledge base maintained by the agent.
Drop files into `raw/`, ask the agent to ingest. Knowledge compounds over time.

```
wiki_dir:  $BASE_DIR/wiki/
raw_dir:   $BASE_DIR/raw/
index:     $BASE_DIR/wiki/index.md
log:       $BASE_DIR/wiki/log.md
hot_cache: $BASE_DIR/wiki/hot.md (500-line limit)
```

**Wiki scripts:**

| Script | Usage | Purpose |
|---|---|---|
| `scripts/wiki/ingest_prep.sh` | `bash ingest_prep.sh <filename>` | Preview raw file + log ingest start |
| `scripts/wiki/new_page.sh` | `bash new_page.sh "<title>" <category>` | Scaffold a new wiki page |
| `scripts/wiki/search_wiki.sh` | `bash search_wiki.sh <query>` | Search all wiki pages |
| `scripts/wiki/lint_wiki.sh` | `bash lint_wiki.sh` | Audit for orphans, broken links, size |

**Categories:** `research/` | `concepts/` | `entities/` | `topics/`

**Ingest a new source:**
```bash
# 1. Drop file into raw/
# 2. Preview it
bash $BASE_DIR/scripts/wiki/ingest_prep.sh myfile.md
# 3. Tell your agent: "Ingest $BASE_DIR/raw/myfile.md into the wiki"
```

**Search the wiki:**
```bash
bash $BASE_DIR/scripts/wiki/search_wiki.sh "mortgage rates"
```

**Standalone install on existing system:**
```bash
bash wiki-install.sh
```
