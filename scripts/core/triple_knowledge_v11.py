#!/usr/bin/env python3
"""
Daily Briefing V10: Direct API Orchestrator
==============================================
Calls Claude, Gemini, and GPT-4o directly via their APIs.
No CLI dependency. No agent sessions. No file polling. No observer.

Usage:
    python3 daily_briefing_v10.py           # Run all 3 engines
    python3 daily_briefing_v10.py G         # Gemini only
    python3 daily_briefing_v10.py A O       # Anthropic + OpenAI
    python3 daily_briefing_v10.py G A       # Gemini + Anthropic
    python3 daily_briefing_v10.py O         # OpenAI only

    Engine codes: G = Gemini, A = Anthropic, O = OpenAI

LinkedIn posts are auto-inserted into the social_posts SQLite table as drafts.

Requirements:
    pip install requests --break-system-packages

Environment variables (set in .bashrc or .env):
    ANTHROPIC_API_KEY=sk-ant-...
    GOOGLE_GEMINI_API_KEY=AI...
    OPENAI_API_KEY=sk-...

Author: ChiefOS
Version: 10.0
"""

import json
import os
import sys
import time
import fcntl
import logging
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BASE_DIR = Path(os.environ.get("BASE_DIR", "/home/chiefos/chiefos"))
DATA_OUT = BASE_DIR / "memory" / "latest_brief.json"
HYDRATOR = BASE_DIR / "scripts" / "hq_briefing_hydrator_v6.py"
LOG_DIR = BASE_DIR / "logs"
DB_PATH = BASE_DIR / os.environ.get("DB_NAME", "chiefos.db")

# Engine code mapping for CLI args
ENGINE_CODES = {
    "G": "gemi",
    "A": "antho",
    "O": "chatty",
}

# API Configuration
ENGINES = [
    {
        "key": "gemi",
        "name": "Gemini",
        "provider": "google",
        "model": "gemini-2.0-flash",
        "env_key": "GOOGLE_GEMINI_API_KEY",
        "info_template": "Gemini 2.0 Flash · Google · {date} · {time} {city}",
    },
    {
        "key": "antho",
        "name": "Agent-C",
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "env_key": "ANTHROPIC_API_KEY",
        "info_template": "Claude Sonnet · Anthropic · {date} · {time} {city}",
    },
    {
        "key": "chatty",
        "name": "Agent-A",
        "provider": "openai",
        "model": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
        "info_template": "GPT-4o · OpenAI · {date} · {time} {city}",
    },
]

# Delay between API calls (seconds) — gentle rate limiting
INTER_ENGINE_DELAY = 10

# Max retries per engine
MAX_RETRIES = 2

# Section definitions (used in the prompt)
SECTIONS = [
    ("s1", "AI Research & Deep Tech"),
    ("s2", "Quantum Computing"),
    ("s3", "Top Technical Creators (YouTube/X)"),
    ("s4", "Reddit AI & Innovation"),
    ("s5", "Local Overview (Weather + Traffic)"),
    ("s6", "Tech News"),
    ("s7", "Canadian News"),
    ("s8", "World News"),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BRIEFING PROMPT — compact, structured, direct JSON output
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_briefing_prompt(display_date: str, engine_name: str) -> str:
    return f"""You are a senior intelligence analyst preparing a daily briefing for a tech executive. Today is {display_date}.

Produce a structured briefing with EXACTLY 8 news sections PLUS 2 LinkedIn post drafts.

NEWS SECTIONS:
1. AI Research & Deep Tech — Top 5 developments in AI/ML research, model releases, architecture breakthroughs
2. Quantum Computing — Top 5 developments in quantum hardware, algorithms, error correction, industry moves
3. Top Technical Creators — Top 5 notable videos/posts from AI YouTubers and X/Twitter thought leaders ([curated AI creator list])
4. Reddit AI & Innovation — Top 5 trending posts from r/LocalLLaMA, r/MachineLearning, r/singularity, r/artificial
5. Local Overview — Item 1: Current weather (temperature, conditions, forecast). Item 2: Traffic conditions (check local major routes)
6. Tech News — Top 5 headlines from TechCrunch, The Verge, Ars Technica, Wired, Reuters Tech
7. National News — Top 5 stories relevant to your country from major national outlets
8. World News — Top 5 major global stories from Reuters, BBC, AP, Al Jazeera

LINKEDIN POSTS (2 posts based on today's most compelling stories):
- "architectural": A deep, analytical post for AI practitioners. Focus on architecture, governance, or infrastructure implications. Tone: authoritative, precise, thought-leadership.
- "flashy": A provocative, attention-grabbing post for a wider audience. Focus on what's surprising or paradigm-shifting. Tone: bold, punchy, designed to stop the scroll.

Each LinkedIn post needs: title, opening (first 2 sentences that hook the reader), body (3-5 sentences of analysis), takeaway (1 sentence closing insight), and hashtags (5-7 relevant hashtags).

Your perspective as {engine_name} should reflect your unique editorial voice and analytical angle. Prioritize differently from other AI models.

RESPOND WITH ONLY valid JSON. No markdown, no backticks, no preamble. The JSON must follow this exact structure:

{{
  "s1": [
    {{"h": "Headline text here", "s": "2-3 sentence analytical summary with your unique perspective"}},
    {{"h": "...", "s": "..."}},
    {{"h": "...", "s": "..."}},
    {{"h": "...", "s": "..."}},
    {{"h": "...", "s": "..."}}
  ],
  "s2": [ ... 5 items ... ],
  "s3": [ ... 5 items ... ],
  "s4": [ ... 5 items ... ],
  "s5": [ ... 2 items: weather then traffic ... ],
  "s6": [ ... 5 items ... ],
  "s7": [ ... 5 items ... ],
  "s8": [ ... 5 items ... ],
  "linkedin": {{
    "architectural": {{
      "title": "Post title here",
      "opening": "First 2 hook sentences",
      "body": "3-5 sentences of analysis",
      "takeaway": "1 sentence closing insight",
      "hashtags": "#Tag1 #Tag2 #Tag3 #Tag4 #Tag5"
    }},
    "flashy": {{
      "title": "Post title here",
      "opening": "First 2 hook sentences",
      "body": "3-5 sentences of analysis",
      "takeaway": "1 sentence closing insight",
      "hashtags": "#Tag1 #Tag2 #Tag3 #Tag4 #Tag5"
    }}
  }}
}}

Critical: Return ONLY the JSON object. No other text."""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def setup_logging(run_id: str) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("tkp")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    log_file = LOG_DIR / f"tkp_run_{run_id}.log"
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)

    latest_link = LOG_DIR / "latest.log"
    try:
        latest_link.unlink(missing_ok=True)
        latest_link.symlink_to(log_file)
    except OSError:
        pass

    return logger


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API CALLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class APIError(Exception):
    """Custom error with status code and body for clear logging."""
    def __init__(self, status_code, body, provider):
        self.status_code = status_code
        self.body = body
        self.provider = provider
        super().__init__(f"{provider} HTTP {status_code}: {body[:200]}")


def call_anthropic(api_key: str, model: str, prompt: str, log: logging.Logger) -> str:
    """Call Anthropic Messages API. Returns raw text response."""
    log.debug(f"    Anthropic API: model={model}")
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise APIError(resp.status_code, resp.text[:500], "Anthropic")
    data = resp.json()
    return "".join(
        block.get("text", "")
        for block in data.get("content", [])
        if block.get("type") == "text"
    )


def call_google(api_key: str, model: str, prompt: str, log: logging.Logger) -> str:
    """Call Google Gemini API. Returns raw text response."""
    log.debug(f"    Google API: model={model}")
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": api_key},
        headers={"content-type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 4096,
                "responseMimeType": "application/json",
            },
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise APIError(resp.status_code, resp.text[:500], "Google")
    data = resp.json()
    candidates = data.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts)
    return ""


def call_openai(api_key: str, model: str, prompt: str, log: logging.Logger) -> str:
    """Call OpenAI Chat Completions API. Returns raw text response."""
    log.debug(f"    OpenAI API: model={model}")
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 4096,
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "You are a senior intelligence analyst. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise APIError(resp.status_code, resp.text[:500], "OpenAI")
    data = resp.json()
    return data.get("choices", [{}])[0].get("message", {}).get("content", "")


# Provider dispatch table
API_CALLERS = {
    "anthropic": call_anthropic,
    "google": call_google,
    "openai": call_openai,
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESPONSE PARSING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def parse_engine_response(raw_text: str, log: logging.Logger) -> dict | None:
    """Parse the JSON response from any engine. Returns sections dict or None."""
    # Strip any markdown fences the model might add despite instructions
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # Remove opening fence (```json or ```)
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        log.error(f"    JSON parse failed: {e}")
        log.debug(f"    Raw response (first 500 chars): {raw_text[:500]}")
        return None

    # Validate structure
    sections = {}
    for sid, _ in SECTIONS:
        items = data.get(sid, [])
        if not isinstance(items, list):
            log.warning(f"    Section {sid}: expected list, got {type(items).__name__}")
            continue

        validated = []
        for item in items:
            if isinstance(item, dict) and "h" in item:
                validated.append({
                    "h": str(item.get("h", "")).strip(),
                    "s": str(item.get("s", "")).strip(),
                })
            else:
                log.warning(f"    Section {sid}: malformed item: {str(item)[:80]}")

        if validated:
            sections[sid] = validated
            log.debug(f"    Section {sid}: {len(validated)} items OK")
        else:
            log.warning(f"    Section {sid}: 0 valid items")

    return sections if sections else None


def parse_linkedin(data: dict, log: logging.Logger) -> dict | None:
    """Extract LinkedIn posts from the parsed JSON. Returns dict or None."""
    li = data.get("linkedin", {})
    if not isinstance(li, dict):
        log.warning("    LinkedIn: not a dict, skipping")
        return None

    result = {}
    for post_type in ("architectural", "flashy"):
        post = li.get(post_type, {})
        if not isinstance(post, dict):
            log.warning(f"    LinkedIn {post_type}: not a dict, skipping")
            continue

        fields = {}
        for field in ("title", "opening", "body", "takeaway", "hashtags"):
            val = str(post.get(field, "")).strip()
            if val:
                fields[field] = val
            else:
                log.warning(f"    LinkedIn {post_type}: missing '{field}'")
                fields[field] = ""

        if fields.get("title"):
            result[post_type] = fields
            log.debug(f"    LinkedIn {post_type}: OK — \"{fields['title'][:50]}\"")

    return result if result else None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LINKEDIN → SQLITE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def insert_linkedin_to_db(linkedin: dict, engine_key: str, log: logging.Logger) -> int:
    """Insert LinkedIn posts into social_posts table as drafts. Returns count inserted."""
    if not DB_PATH.exists():
        log.warning(f"  ├─ DB not found ({DB_PATH}), skipping LinkedIn insert")
        return 0

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    now_iso = now.isoformat()
    inserted = 0

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Check which columns exist (handles old schema gracefully)
        cursor.execute("PRAGMA table_info(social_posts)")
        existing_cols = {row[1] for row in cursor.fetchall()}

        for post_type, post in linkedin.items():
            title = post.get("title", "")
            if not title:
                continue

            # Check for duplicate (same title + same date = already inserted)
            cursor.execute(
                "SELECT id FROM social_posts WHERE title = ? AND post_date = ?",
                (title, date_str),
            )
            if cursor.fetchone():
                log.debug(f"    LinkedIn {post_type}: already in DB, skipping")
                continue

            # Build insert based on available columns — use next numeric ID
            cursor.execute("SELECT MAX(CAST(id AS INTEGER)) FROM social_posts WHERE id GLOB '[0-9]*'")
            max_id = cursor.fetchone()[0] or 0
            post_id = str(max_id + 1)
            fields = {"id": post_id, "title": title, "platform": "LinkedIn", "status": "Draft", "post_date": date_str}

            # Add extended fields if columns exist
            if "opening" in existing_cols:
                fields["opening"] = post.get("opening", "")
            if "body" in existing_cols:
                fields["body"] = post.get("body", "")
            if "takeaway" in existing_cols:
                fields["takeaway"] = post.get("takeaway", "")
            if "hashtags" in existing_cols:
                fields["hashtags"] = post.get("hashtags", "")
            if "post_type" in existing_cols:
                fields["post_type"] = post_type
            if "engine" in existing_cols:
                fields["engine"] = engine_key
            if "created_at" in existing_cols:
                fields["created_at"] = now_iso
            if "updated_at" in existing_cols:
                fields["updated_at"] = now_iso

            cols = ", ".join(fields.keys())
            placeholders = ", ".join(["?"] * len(fields))
            cursor.execute(
                f"INSERT INTO social_posts ({cols}) VALUES ({placeholders})",
                list(fields.values()),
            )
            inserted += 1

        conn.commit()
        conn.close()

    except sqlite3.OperationalError as e:
        log.error(f"  ├─ DB error inserting LinkedIn posts: {e}")
        return 0

    return inserted


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# JSON FILE OPERATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def write_master_json(data: dict, log: logging.Logger) -> bool:
    """Atomic write with file locking."""
    DATA_OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = DATA_OUT.with_suffix(".tmp")
    try:
        with open(tmp_path, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            json.dump(data, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
            fcntl.flock(f, fcntl.LOCK_UN)
        tmp_path.rename(DATA_OUT)
        return True
    except OSError as e:
        log.error(f"  Failed to write JSON: {e}")
        tmp_path.unlink(missing_ok=True)
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN ORCHESTRATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging(run_id)
    run_start = time.time()

    now = datetime.now()
    display_date = now.strftime("%A, %B %d, %Y").upper()
    date_short = now.strftime("%B %d, %Y")
    time_short = now.strftime("%I:%M %p")

    # ── Parse engine selector from CLI args ────────────────
    args = [a.upper() for a in sys.argv[1:]]
    if args:
        selected_keys = []
        for code in args:
            if code in ENGINE_CODES:
                selected_keys.append(ENGINE_CODES[code])
            else:
                print(f"❌ Unknown engine code: {code}")
                print("   Valid codes: G = Gemini, A = Anthropic, O = OpenAI")
                print("   Example: python3 daily_briefing_v10.py G O")
                sys.exit(2)
        active_engines = [e for e in ENGINES if e["key"] in selected_keys]
    else:
        active_engines = ENGINES

    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("  🚀 TRIPLE KNOWLEDGE V10: DIRECT API")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info(f"  Run ID:   {run_id}")
    log.info(f"  Date:     {display_date}")
    log.info(f"  Engines:  {', '.join(e['name'] for e in active_engines)}")
    if args:
        log.info(f"  Selector: {' '.join(args)}")
    log.info("")

    # ── Pre-flight: Check API keys for selected engines ────
    missing_keys = []
    for engine in active_engines:
        if not os.environ.get(engine["env_key"]):
            missing_keys.append(f"{engine['name']}: ${engine['env_key']}")

    if missing_keys:
        log.critical("  ❌ Missing API keys:")
        for mk in missing_keys:
            log.critical(f"     • {mk}")
        log.critical("")
        log.critical("  Set them in your environment or .bashrc:")
        log.critical("  export ANTHROPIC_API_KEY=sk-ant-...")
        log.critical("  export GOOGLE_GEMINI_API_KEY=AI...")
        log.critical("  export OPENAI_API_KEY=sk-...")
        sys.exit(2)

    log.info("  ✅ All API keys present")
    log.info("")

    # ── Load existing master JSON (preserve other engines) ─
    if DATA_OUT.exists() and args:
        try:
            with open(DATA_OUT, "r") as f:
                master = json.load(f)
            master["run_id"] = run_id
            master["display_date"] = display_date
            log.info("  📄 Loaded existing master JSON (preserving other engines)")
        except (json.JSONDecodeError, OSError):
            master = {"date": now.strftime("%Y-%m-%d"), "display_date": display_date, "run_id": run_id, "engines": {}}
    else:
        master = {"date": now.strftime("%Y-%m-%d"), "display_date": display_date, "run_id": run_id, "engines": {}}

    # ── Call each engine ───────────────────────────────────
    engine_results = {}
    total_engines = len(active_engines)

    for idx, engine in enumerate(active_engines):
        key = engine["key"]
        name = engine["name"]
        provider = engine["provider"]
        model = engine["model"]
        api_key = os.environ.get(engine["env_key"], "")

        if idx > 0:
            log.info(f"  ⏳ Cooling down {INTER_ENGINE_DELAY}s...")
            time.sleep(INTER_ENGINE_DELAY)

        log.info(f"  ╭─────────────────────────────────────────")
        log.info(f"  │ ENGINE {idx+1}/{total_engines}: {name.upper()} ({model})")
        log.info(f"  ╰─────────────────────────────────────────")

        prompt = build_briefing_prompt(display_date, name)
        log.info(f"  ├─ Prompt: {len(prompt)} chars (~{len(prompt)//4} tokens)")

        caller = API_CALLERS[provider]
        result = {"sections": 0, "complete": False, "error": None}
        engine_start = time.time()

        for attempt in range(1, MAX_RETRIES + 1):
            if attempt > 1:
                log.info(f"  ├─ 🔄 Retry {attempt}/{MAX_RETRIES} (waiting 15s)...")
                time.sleep(15)

            try:
                log.info(f"  ├─ 📡 Calling {provider} API...")
                raw_response = caller(api_key, model, prompt, log)

                log.info(f"  ├─ 📥 Response: {len(raw_response)} chars")
                log.debug(f"  │  First 200 chars: {raw_response[:200]}")

                sections = parse_engine_response(raw_response, log)
                if not sections:
                    log.warning(f"  ├─ ⚠️  Parse returned no sections")
                    result["error"] = "parse_failed"
                    continue

                # Parse LinkedIn posts from the same response
                try:
                    cleaned_for_li = raw_response.strip()
                    if cleaned_for_li.startswith("```"):
                        cleaned_for_li = cleaned_for_li.split("\n", 1)[1] if "\n" in cleaned_for_li else cleaned_for_li[3:]
                    if cleaned_for_li.endswith("```"):
                        cleaned_for_li = cleaned_for_li[:-3]
                    full_data = json.loads(cleaned_for_li.strip())
                    linkedin = parse_linkedin(full_data, log)
                except (json.JSONDecodeError, Exception):
                    linkedin = None

                # Build engine entry
                section_count = len(sections)
                engine_info = engine["info_template"].format(
                    date=date_short, time=time_short
                )

                engine_entry = {
                    "status": "COMPLETE" if section_count == 8 else f"PARTIAL ({section_count}/8)",
                    "info": engine_info,
                    "sections": {
                        sid: {"items": items, "parsed_at": datetime.now().isoformat()}
                        for sid, items in sections.items()
                    },
                    "completed_at": datetime.now().isoformat(),
                }

                if linkedin:
                    engine_entry["linkedin"] = linkedin
                    log.info(f"  ├─ 📣 LinkedIn: {len(linkedin)} posts parsed")

                    # Auto-insert into SQLite as drafts
                    db_count = insert_linkedin_to_db(linkedin, key, log)
                    if db_count > 0:
                        log.info(f"  ├─ 💾 LinkedIn: {db_count} new drafts inserted into DB")

                master["engines"][key] = engine_entry

                result = {
                    "sections": section_count,
                    "complete": section_count == 8,
                    "error": None,
                }

                log.info(f"  ├─ ✅ {section_count}/8 sections parsed")
                break  # success, move to next engine

            except requests.exceptions.Timeout:
                log.error(f"  ├─ ❌ API timeout (120s)")
                result["error"] = "timeout"

            except APIError as e:
                log.error(f"  ├─ ❌ HTTP {e.status_code}: {e.body[:300]}")
                result["error"] = f"http_{e.status_code}"

                # Don't retry on auth errors
                if e.status_code in (401, 403):
                    log.error(f"  ├─ Auth error — check ${engine['env_key']}")
                    break

                # Don't retry on quota errors
                if e.status_code == 429:
                    log.error(f"  ├─ Quota/rate limit — check billing for {engine['name']}")
                    break

            except requests.exceptions.ConnectionError as e:
                log.error(f"  ├─ ❌ Connection error: {e}")
                result["error"] = "connection"

            except Exception as e:
                log.error(f"  ├─ ❌ Unexpected error: {type(e).__name__}: {e}")
                result["error"] = str(e)

        engine_elapsed = time.time() - engine_start
        log.info(f"  ├─ Finished in {engine_elapsed:.1f}s")
        log.info("")
        engine_results[key] = result

    # ── Write master JSON ──────────────────────────────────
    if write_master_json(master, log):
        log.info(f"  📄 Master JSON written: {DATA_OUT}")
    else:
        log.error("  ❌ Failed to write master JSON")
        sys.exit(2)

    # ── Run hydrator ───────────────────────────────────────
    log.info("")
    log.info("  💧 Running hydrator...")

    if HYDRATOR.exists():
        import subprocess
        try:
            hydrate = subprocess.run(
                ["python3", str(HYDRATOR)],
                capture_output=True, text=True, timeout=60,
            )
            if hydrate.returncode == 0:
                log.info("  ✅ Hydrator completed")
                if hydrate.stdout.strip():
                    log.debug(f"  Hydrator output: {hydrate.stdout.strip()[:300]}")
            else:
                log.error(f"  ❌ Hydrator failed (exit {hydrate.returncode})")
                log.error(f"  stderr: {hydrate.stderr.strip()[:500]}")
        except subprocess.TimeoutExpired:
            log.error("  ❌ Hydrator timed out (60s)")
        except OSError as e:
            log.error(f"  ❌ Hydrator error: {e}")
    else:
        log.warning(f"  ⚠️  Hydrator not found: {HYDRATOR}")

    # ── Hydrate posts page ─────────────────────────────────
    CONTENT_HYDRATOR = BASE_DIR / "scripts" / "hydrate_content.py"
    log.info("  💧 Refreshing posts data...")
    if CONTENT_HYDRATOR.exists():
        try:
            hydrate_posts = subprocess.run(
                ["python3", str(CONTENT_HYDRATOR)],
                capture_output=True, text=True, timeout=60,
            )
            if hydrate_posts.returncode == 0:
                log.info("  ✅ Posts data refreshed")
                if hydrate_posts.stdout.strip():
                    log.debug(f"  Posts hydrator output: {hydrate_posts.stdout.strip()[:300]}")
            else:
                log.error(f"  ❌ Posts hydrator failed (exit {hydrate_posts.returncode})")
                log.error(f"  stderr: {hydrate_posts.stderr.strip()[:500]}")
        except subprocess.TimeoutExpired:
            log.error("  ❌ Posts hydrator timed out (60s)")
        except OSError as e:
            log.error(f"  ❌ Posts hydrator error: {e}")
    else:
        log.warning(f"  ⚠️  Posts hydrator not found: {CONTENT_HYDRATOR}")

    # ── Run summary ────────────────────────────────────────
    total_time = time.time() - run_start
    total_sections = sum(r["sections"] for r in engine_results.values())
    max_sections = total_engines * 8

    log.info("")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("  RUN SUMMARY")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info(f"  Run ID:     {run_id}")
    log.info(f"  Duration:   {total_time:.1f}s ({total_time/60:.1f}m)")
    log.info(f"  Log:        {LOG_DIR / f'tkp_run_{run_id}.log'}")
    log.info("")

    for key, r in engine_results.items():
        icon = "✅" if r["complete"] else "⚠️" if r["sections"] > 0 else "❌"
        err = r["error"] or "OK"
        log.info(f"  {icon} {key.upper():8s} — {r['sections']}/8 sections | {err}")

    log.info("")
    log.info(f"  Total:  {total_sections}/{max_sections} sections")
    overall = "✅ FULL SUCCESS" if total_sections == max_sections else "⚠️  PARTIAL" if total_sections > 0 else "❌ FAILED"
    log.info(f"  Result: {overall}")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Exit code
    if total_sections == 0:
        sys.exit(2)
    elif total_sections < max_sections:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
