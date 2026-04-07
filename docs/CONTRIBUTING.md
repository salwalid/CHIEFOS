# Contributing to ChiefOS

Thanks for your interest in contributing. ChiefOS is a pragmatic project — contributions should make it more useful, more reliable, or easier to install. No gold-plating.

---

## What We're Looking For

**Great contributions:**
- Bug fixes with a clear reproduction case
- New alert scripts for common domains (debt tracking, health, fitness, vehicles)
- New dashboard pages for Domain 6 (Projects), Domain 7 (Comms), Domain 9 (Vault)
- New alert channels (Slack, email, webhook) as drop-in replacements for `send_alert.sh`
- Installer improvements for non-Ubuntu Linux (CentOS, Arch)
- Windows/WSL2 support

**Out of scope:**
- Breaking changes to `social_posts` table name (briefing engine dependency)
- Breaking changes to `add_todo.py` CLI interface
- Changes that require users to edit generated files manually
- Features that only work with one specific AI model

---

## Development Setup

```bash
git clone https://github.com/YOUR/CHIEFOS.git
cd CHIEFOS

# Set up a local test database
cp config.env.template config.env
# Edit config.env — set BASE_DIR to a local path
sqlite3 ./test.db < setup/schema.sql
sqlite3 ./test.db < setup/seed_data.sql
```

Run scripts directly for testing:
```bash
BASE_DIR=$(pwd) DB_NAME=test.db python3 scripts/core/hydrate_finance.py
```

---

## Code Style

**Python:**
- Standard library only where possible — no new package dependencies without strong justification
- Scripts are standalone — each script sources its own config, no shared module imports across scripts
- `BASE_DIR = os.environ.get("BASE_DIR", "/home/chiefos/chiefos")` at the top — always reads from env
- No hardcoded paths, emails, usernames, or credentials anywhere

**Shell:**
- `set -euo pipefail` at the top of every script
- Source `load_env.sh` before using any env vars
- Prefer `"${VAR:-default}"` over bare `$VAR`
- Quote all paths: `"$BASE_DIR/path/to/file"`

**New scripts:**
- Place in the correct subdirectory: `core/`, `alerts/`, `utils/`
- Must be executable: `chmod +x`
- Must work when called with no arguments (show usage or exit cleanly)

---

## Adding a New Alert Script

1. Create `scripts/alerts/my_alert.py` following the pattern of `bill_reminder.py`
2. Read config from env: `BASE_DIR`, `DB_NAME`, `ALERT_SCRIPT`
3. Write the alert message to a temp file, call `send_alert.sh`
4. Add to the crontab section of `install.sh`
5. Document in `docs/DOMAINS.md` under the relevant domain

---

## Adding a New Dashboard Page

1. Create `www/HQ/my_domain/index.html`
2. Create `scripts/core/hydrate_my_domain.py` — reads DB, writes `my_domain_data.json`
3. The HTML page fetches the JSON and renders it; auto-refreshes every 60s
4. Add the hydrator to `scripts/core/master_hydration.sh`
5. Document in `docs/DOMAINS.md`

---

## Pull Request Process

1. Fork the repo and create a branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Test against a fresh database: `sqlite3 test.db < setup/schema.sql`
4. Run a spot-check for personal values: `grep -r "hardcoded_thing" scripts/ www/`
5. Open a PR with:
   - What it does (one paragraph)
   - How to test it
   - Any new config.env variables needed

---

## Reporting Bugs

Open an issue with:
- Your OS and Python version
- The exact error message or unexpected behavior
- Steps to reproduce

If the bug involves credentials or personal data, redact before posting.

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
