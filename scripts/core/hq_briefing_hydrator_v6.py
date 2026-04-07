#!/usr/bin/env python3
"""
HQ Briefing Hydrator V6
========================
Reads latest_brief.json and renders the HQ briefing HTML dashboard.

Fixes over V3:
- Template-based: always renders from the original template, not the last output.
  This means it works on EVERY run, not just the first.
- Hardcoded date replaced with a marker system.
- Proper error handling and logging.
- Backs up the previous HTML before overwriting.
- Validates JSON structure before rendering.
- Reports what was injected vs what was missing.

Author: ChiefOS
Version: 6.0
"""

import json
import os
import re
import sys
import shutil
import logging
from datetime import datetime
from pathlib import Path

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BASE_DIR = Path(os.environ.get("BASE_DIR", "/home/chiefos/chiefos"))
DATA_PATH = BASE_DIR / "memory" / "latest_brief.json"

# IMPORTANT: The template is the SOURCE OF TRUTH with all <!-- markers --> intact.
# The output is the rendered copy. Never read from output to render.
HTML_TEMPLATE = BASE_DIR / "www" / "HQ" / "briefing" / "template.html"
HTML_OUTPUT = BASE_DIR / "www" / "HQ" / "briefing" / "index.html"
HTML_BACKUP_DIR = BASE_DIR / "www" / "HQ" / "briefing" / "backups"

# Date marker in the template (replaces the hardcoded date approach)
DATE_MARKER = "<!-- display-date -->"

# Fallback: if no marker exists, try regex against common date formats
DATE_REGEX_FALLBACK = re.compile(
    r"(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)"
    r",\s+(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|"
    r"SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+\d{1,2},\s+\d{4}"
)

# Known engines and sections
EXPECTED_ENGINES = ["gemi", "antho", "chatty"]
EXPECTED_SECTIONS = [f"s{i}" for i in range(1, 9)]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
log = logging.getLogger("hydrator")
log.setLevel(logging.DEBUG)

_ch = logging.StreamHandler(sys.stdout)
_ch.setLevel(logging.INFO)
_ch.setFormatter(logging.Formatter("%(message)s"))
log.addHandler(_ch)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VALIDATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def validate_brief(brief: dict) -> list[str]:
    """Validate the briefing JSON and return a list of warnings."""
    warnings = []

    if "display_date" not in brief:
        warnings.append("Missing 'display_date' field")

    if "engines" not in brief or not isinstance(brief.get("engines"), dict):
        warnings.append("Missing or invalid 'engines' field")
        return warnings

    for engine_key in EXPECTED_ENGINES:
        if engine_key not in brief["engines"]:
            warnings.append(f"Engine '{engine_key}' not found in data")
            continue

        engine = brief["engines"][engine_key]
        sections = engine.get("sections", {})

        if not sections:
            warnings.append(f"Engine '{engine_key}' has no sections")
            continue

        for sid in EXPECTED_SECTIONS:
            if sid not in sections:
                warnings.append(f"Engine '{engine_key}' missing section '{sid}'")
            else:
                items = sections[sid].get("items", [])
                if not items:
                    warnings.append(f"Engine '{engine_key}' section '{sid}' has 0 items")
                else:
                    for idx, item in enumerate(items):
                        if not item.get("h"):
                            warnings.append(
                                f"Engine '{engine_key}' {sid} item {idx+1}: empty headline"
                            )

    return warnings


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HTML SANITIZATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def sanitize_html(text: str) -> str:
    """Escape HTML entities in user-provided text to prevent XSS."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HYDRATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def hydrate():
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("  💧 HQ BRIEFING HYDRATOR V6")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # ── Load JSON ──────────────────────────────────────────
    if not DATA_PATH.exists():
        log.error(f"  ❌ No data found at {DATA_PATH}")
        sys.exit(1)

    try:
        with open(DATA_PATH, "r") as f:
            brief = json.load(f)
    except json.JSONDecodeError as e:
        log.error(f"  ❌ Corrupt JSON: {e}")
        sys.exit(1)

    log.info(f"  📄 Loaded: {DATA_PATH}")
    log.info(f"  📅 Date: {brief.get('display_date', 'UNKNOWN')}")
    log.info(f"  🔑 Run ID: {brief.get('run_id', 'N/A')}")

    # ── Validate ───────────────────────────────────────────
    warnings = validate_brief(brief)
    if warnings:
        log.warning(f"  ⚠️  {len(warnings)} validation warnings:")
        for w in warnings:
            log.warning(f"     • {w}")
    else:
        log.info("  ✅ Data validation passed (all 3 engines × 8 sections)")

    # ── Load HTML Template ─────────────────────────────────
    if not HTML_TEMPLATE.exists():
        # First-time migration: if no template exists but index.html does,
        # assume the current index.html IS the template and copy it.
        if HTML_OUTPUT.exists():
            log.warning("  ⚠️  No template.html found — creating from current index.html")
            shutil.copy2(HTML_OUTPUT, HTML_TEMPLATE)
        else:
            log.error(f"  ❌ Neither template nor output HTML found")
            sys.exit(1)

    try:
        with open(HTML_TEMPLATE, "r") as f:
            html = f.read()
    except OSError as e:
        log.error(f"  ❌ Failed to read template: {e}")
        sys.exit(1)

    log.info(f"  📝 Template loaded: {HTML_TEMPLATE} ({len(html)} chars)")

    # ── Backup Current Output ──────────────────────────────
    if HTML_OUTPUT.exists():
        HTML_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = HTML_BACKUP_DIR / f"index_{ts}.html"
        shutil.copy2(HTML_OUTPUT, backup_path)
        log.info(f"  💾 Backed up previous: {backup_path.name}")

        # Keep only last 7 backups
        backups = sorted(HTML_BACKUP_DIR.glob("index_*.html"), reverse=True)
        for old in backups[7:]:
            old.unlink()
            log.debug(f"  Pruned old backup: {old.name}")

    # ── Inject Display Date ────────────────────────────────
    display_date = brief.get("display_date", datetime.now().strftime("%A, %B %d, %Y").upper())
    injections = 0

    if DATE_MARKER in html:
        html = html.replace(DATE_MARKER, sanitize_html(display_date))
        injections += 1
        log.info(f"  📅 Date injected via marker")
    else:
        # Fallback: regex replace any existing date string
        if DATE_REGEX_FALLBACK.search(html):
            html = DATE_REGEX_FALLBACK.sub(sanitize_html(display_date), html)
            injections += 1
            log.info(f"  📅 Date injected via regex fallback")
        else:
            log.warning("  ⚠️  No date marker or date pattern found in template")

    # ── Inject Engine Data ─────────────────────────────────
    for agent_id, agent_data in brief.get("engines", {}).items():
        sections = agent_data.get("sections", {})
        if not sections:
            log.warning(f"  ⚠️  {agent_id.upper()}: no sections to inject")
            continue

        # Agent info line
        info_marker = f"<!-- {agent_id}-info -->"
        info_text = agent_data.get("info", f"{agent_id.upper()}")
        if info_marker in html:
            html = html.replace(info_marker, sanitize_html(info_text))
            injections += 1

        # Section headlines and summaries
        section_count = 0
        item_count = 0

        for sid, sdata in sections.items():
            items = sdata.get("items", [])
            if not items:
                continue
            section_count += 1

            for i, item in enumerate(items):
                num = i + 1
                h_marker = f"<!-- {agent_id}-{sid}-h{num} -->"
                s_marker = f"<!-- {agent_id}-{sid}-s{num} -->"

                headline = item.get("h", "")
                summary = item.get("s", "")

                if h_marker in html:
                    html = html.replace(h_marker, sanitize_html(headline))
                    injections += 1
                    item_count += 1
                else:
                    log.debug(f"    Marker not found: {h_marker}")

                if s_marker in html:
                    html = html.replace(s_marker, sanitize_html(summary))
                    injections += 1
                else:
                    log.debug(f"    Marker not found: {s_marker}")

        status = agent_data.get("status", "UNKNOWN")
        log.info(f"  🤖 {agent_id.upper():8s} — {section_count} sections, {item_count} headlines | {status}")

        # LinkedIn posts
        linkedin = agent_data.get("linkedin", {})
        if linkedin:
            li_count = 0
            type_map = {"architectural": "arch", "flashy": "flash"}
            for post_type, short in type_map.items():
                post = linkedin.get(post_type, {})
                if not post:
                    continue
                for field in ("title", "opening", "body", "takeaway", "hashtags"):
                    marker = f"<!-- {agent_id}-li-{short}-{field} -->"
                    value = post.get(field, "")
                    if marker in html and value:
                        html = html.replace(marker, sanitize_html(value))
                        injections += 1
                        li_count += 1
            if li_count > 0:
                log.info(f"  📣 {agent_id.upper():8s} — {li_count} LinkedIn fields injected")

    # ── Inject Compare Panel Data ──────────────────────────
    # Compare markers use format: <!-- cmp-{agent}-{sid}-h{n} -->
    cmp_injections = 0
    for agent_id, agent_data in brief.get("engines", {}).items():
        sections = agent_data.get("sections", {})
        for sid, sdata in sections.items():
            items = sdata.get("items", [])
            for i, item in enumerate(items):
                num = i + 1
                cmp_h = f"<!-- cmp-{agent_id}-{sid}-h{num} -->"
                cmp_s = f"<!-- cmp-{agent_id}-{sid}-s{num} -->"
                if cmp_h in html:
                    html = html.replace(cmp_h, sanitize_html(item.get("h", "")))
                    cmp_injections += 1
                if cmp_s in html:
                    html = html.replace(cmp_s, sanitize_html(item.get("s", "")))
                    cmp_injections += 1
    if cmp_injections > 0:
        log.info(f"  🔀 Compare panel: {cmp_injections} injections")
    injections += cmp_injections

    # ── Write Output ───────────────────────────────────────
    try:
        HTML_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with open(HTML_OUTPUT, "w") as f:
            f.write(html)
    except OSError as e:
        log.error(f"  ❌ Failed to write output: {e}")
        sys.exit(1)

    log.info("")
    log.info(f"  ✅ Hydration complete: {injections} injections")
    log.info(f"  📍 Output: {HTML_OUTPUT}")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    hydrate()
