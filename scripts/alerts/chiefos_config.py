"""
chiefos_config.py — Shared config for ChiefOS alerting scripts.

Reads tunables from environment variables (set in config.env) with safe
defaults. Used by todo_alert.py and lead_up_checks.py.
"""
import os

BASE_DIR = os.environ.get("BASE_DIR", "/home/chiefos/chiefos")
DB_NAME = os.environ.get("DB_NAME", "chiefos.db")
DB_PATH = os.path.join(BASE_DIR, DB_NAME)

ALERT_SCRIPT = os.environ.get(
    "ALERT_SCRIPT", os.path.join(BASE_DIR, "scripts/utils/send_alert.sh")
)
HYDRATE_SCHEDULE = os.path.join(BASE_DIR, "scripts/core/hydrate_schedule.py")

BASE_URL = os.environ.get("BASE_URL", "yourdomain.com")
DASHBOARD_URL = f"https://{BASE_URL}/HQ/schedule/"

HORIZON_DAYS = int(os.environ.get("HORIZON_DAYS", "5"))

CAP_OVERDUE = int(os.environ.get("CAP_OVERDUE", "5"))
CAP_TODAY = int(os.environ.get("CAP_TODAY", "10"))
CAP_HORIZON = int(os.environ.get("CAP_HORIZON", "8"))


def _csv_int(name, default):
    raw = os.environ.get(name, default)
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def _csv_str(name, default):
    raw = os.environ.get(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


LEAD_UP_DAYS = _csv_int("LEAD_UP_DAYS", "3,1")
LEAD_UP_PRIORITIES = _csv_str("LEAD_UP_PRIORITIES", "high")

CATEGORY_EMOJI = {
    "project":  "🚀",
    "finance":  "💰",
    "property": "🏠",
    "content":  "📢",
    "personal": "👤",
}

PRIORITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}

ACTIVE_STATUSES = ("open", "in_progress")
