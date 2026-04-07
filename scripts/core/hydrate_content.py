#!/usr/bin/env python3
"""
hydrate_content.py — Replaces hydrate_posts_v1.py
Reads social_posts from SQLite → writes posts_data.json for the frontend.
Includes platform breakdown (linkedin, blog, other).
"""

import sqlite3
import json
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(os.environ.get("BASE_DIR", "/home/chiefos/chiefos"))
DB_PATH = BASE_DIR / os.environ.get("DB_NAME", "chiefos.db")
OUTPUT_PATH = BASE_DIR / "www" / "HQ" / "posts" / "posts_data.json"


def hydrate():
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute("SELECT * FROM social_posts ORDER BY id DESC").fetchall()
        posts = [dict(row) for row in rows]

        # Platform breakdown
        by_platform = {}
        for p in posts:
            platform = p.get("platform") or "other"
            by_platform.setdefault(platform, []).append(p)

        output = {
            "sync_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(posts),
            "posts": posts,
            "by_platform": by_platform,
            "platform_counts": {k: len(v) for k, v in by_platform.items()}
        }

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w") as f:
            json.dump(output, f, indent=2)

        total = len(posts)
        drafts = sum(1 for p in posts if p.get("status") in ("Draft", "DRAFT"))
        published = sum(1 for p in posts if p.get("status") in ("Published", "PUBLISHED"))
        counts = ", ".join(f"{k}={len(v)}" for k, v in by_platform.items())
        print(f"✅ {total} posts hydrated ({drafts} draft, {published} published) [{counts}] → {OUTPUT_PATH}")

    except sqlite3.OperationalError as e:
        print(f"❌ DB error: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    hydrate()
