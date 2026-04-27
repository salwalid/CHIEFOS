# ChiefOS — The 10 Domains

ChiefOS organizes your life and business into 10 operational domains.
Each domain has a dedicated HQ dashboard, one or more database tables, and alert scripts that fire when action is needed.

---

## Domain 1 — Briefing

**Dashboard:** `/HQ/briefing/`
**Powered by:** `daily_briefing_v11.py` + `hq_briefing_hydrator_v6.py`
**Cron:** 4:00am daily

The morning intelligence brief. Synthesizes overnight activity across all domains — outstanding todos, upcoming events, financial alerts, security events — into a single executive summary. Runs before you wake up, ready when you open your laptop.

**Tables:** `todos`, `events`, `financial_transactions`, `projects`, `chronicles`

---

## Domain 2 — Finance

**Dashboard:** `/HQ/finance/`
**Powered by:** `hydrate_finance.py`
**Alerts:** `bill_reminder.py` (5am daily), `deposit_reminder.py` (5am daily), `monthly_summary.py` (last day of month)

Tracks all money in and out. Income from properties, expenses by category, upcoming bills, and subscription charges. The 14-day bill horizon ensures you never pay late — alerts fire with enough lead time for bank transfers.

**Tables:** `financial_transactions`, `subscriptions`

**Key design:** Positive `amount` = income, negative = expense. Category values: `rent`, `mortgage`, `repair`, `tax`, `insurance`, `utilities`, `personal`, `other`.

---

## Domain 3 — Property

**Dashboard:** `/HQ/property/`
**Powered by:** `hydrate_properties.py`
**Alerts:** `maintenance_tracker.py` (5am daily)

All real estate assets in one view. Occupancy status, cleaning status, last maintenance date, upcoming tax deadlines, and critical notes. Maintenance jobs are tracked in `maintenance_log` with contractor assignments and cost tracking.

**Tables:** `properties`, `maintenance_log`, `contacts`, `property_utilities`

---

## Domain 4 — Schedule

**Dashboard:** `/HQ/schedule/`
**Powered by:** `hydrate_schedule.py`
**Alerts:** `todo_alert.py` (5:30am daily), `weekly_preview.py` (5:45am daily + Sunday 8pm)

The operational calendar. Shows all todos with due dates and all events in a unified view. Auto-refreshes every 60 seconds. Always current — `add_todo.py` triggers a hydration immediately on insert so items appear within 60 seconds.

**Tables:** `todos`, `events`

**Critical rule:** Always use `add_todo.py` to create todos. Direct SQL inserts skip the real-time hydration.

---

## Domain 5 — Content

**Dashboard:** `/HQ/posts/`
**Powered by:** `hydrate_content.py`
**Alerts:** none (content pipeline is pull, not push)

Content pipeline across platforms. Tracks posts by platform (`linkedin`, `blog`, `instagram`) and status (`DRAFT`, `SCHEDULED`, `PUBLISHED`, `ARCHIVED`). The briefing engine pulls published counts into the daily brief.

**Tables:** `social_posts`

**Note:** `social_posts` must not be renamed — the briefing engine depends on the exact table name.

---

## Domain 6 — Projects

**Dashboard:** `/HQ/projects/`
**Powered by:** `hydrate_projects.py`
**Alerts:** `project_status.py` (Monday 9am)

Active initiatives and their work items. Projects contain tasks; tasks link to todos for deadline tracking. Every Monday, a project status alert fires summarizing active projects, their status, and any overdue tasks.

**Tables:** `projects`, `tasks`, `todos` (linked via `linked_type='tasks'`)

**Key design:** A task needs a linked todo with a `due_date` to appear on the Schedule calendar. Create the task first, then create a todo linked to it.

---

## Domain 7 — Communications

**Dashboard:** `/HQ/comms/`
**Powered by:** `hydrate_comms.py`, `check_emails.py`, `morning_email_review.py`
**Alerts:** `morning_email_review.py` (5am daily)

Email monitoring and communications tracking. `check_emails.py` runs every 30 minutes to check for new messages and log them. `morning_email_review.py` sends a daily digest of overnight emails — counts, senders, anything flagged urgent.

**Tables:** `table_Alpha_Intel` (last_email_id tracking), `contacts`

---

## Domain 8 — Security

**Dashboard:** `/HQ/security/`
**Powered by:** `hydrate_security.py`, `cron-security-monitor.sh`, `executive-security-summary.sh`
**Alerts:** Security monitor runs 3x daily (7am, 12pm, 8pm); executive summary at 4:15pm

Network perimeter monitoring. Logs login attempts, failed auth, Fail2Ban bans, and suspicious IPs. The executive summary provides a daily digest of security events with ISP resolution.

**Tables:** `security_events`

---

## Domain 9 — Knowledge

**Dashboard:** `/HQ/vault/` *(planned)*
**Powered by:** `hydrate_vault.py`

Strategic concepts, breakthroughs, and domain knowledge. When your agent learns something important — a decision framework, a lesson from a failure, a key insight — it goes in the vault. Searchable, categorized, tagged.

**Tables:** `context_vault`, `chronicles`

---

## Domain 10 — Travel & Events

**Dashboard:** shown on Schedule (`/HQ/schedule/`)
**Powered by:** `hydrate_schedule.py`

Travel plans, meetings, deadlines, and important dates. Stored in `events` and rendered on the Schedule calendar alongside todos. Travel events display a detail line with 📍 location and notes directly beneath the event tag. Travel domain is handled directly by the COS Agent (no dedicated sub-agent).

**Tables:** `events`

**Event types:** `travel`, `meeting`, `deadline`, `personal`, `property`

---

## Cross-Domain Architecture

The `todos` table is the backbone connecting all domains:

```
Domain          Table                   → todos (due_date + reminder_date)
─────────────────────────────────────────────────────
Property        properties              → maintenance reminders, tax dates
Finance         subscriptions           → bill due dates
Finance         financial_transactions  → deposit expected dates
Projects        tasks                   → task deadlines
Content         social_posts            → post scheduled dates
Events          events                  → event reminders
```

Every time something has a deadline or reminder, it creates a `todo` linked back to its source row via `linked_type` + `linked_id`. This is what powers the unified Schedule calendar and all alert scripts.
