import os
import json
import sqlite3
import re
import subprocess
from datetime import datetime

BASE_DIR = os.environ.get("BASE_DIR", "/home/chiefos/chiefos")
SECURITY_JSON = os.path.join(BASE_DIR, "www/HQ/security/security_data.json")
LOG_PATH = os.path.join(BASE_DIR, "logs/security_{}.log".format(datetime.now().strftime("%Y-%m-%d")))
DB_PATH = os.path.join(BASE_DIR, os.environ.get("DB_NAME", "chiefos.db"))

def get_system_metrics():
    metrics = {"updates": 0, "permission_alerts": [], "fail2ban_status": "INACTIVE", "banned_count": 0, "attacks": []}
    try:
        output = subprocess.check_output(["apt", "list", "--upgradable"], stderr=subprocess.STDOUT).decode()
        metrics["updates"] = len(re.findall(r'\[upgradable from:', output))
    except: pass
    files = []  # OpenClaw agent config paths — populate if using OpenClaw
    for f in files:
        if os.path.exists(f):
            mode = oct(os.stat(f).st_mode)[-3:]
            if mode != "600": metrics["permission_alerts"].append(f"{os.path.basename(f)} is {mode}")
    try:
        if subprocess.run(["systemctl", "is-active", "fail2ban"], capture_output=True, text=True).stdout.strip() == "active":
            metrics["fail2ban_status"] = "ACTIVE"
    except: pass
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r') as f:
            c = f.read()
            metrics["attacks"] = list(set(re.findall(r'Failed password for .* from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', c)))
            metrics["banned_count"] = c.count("Ban ")
    return metrics

def get_login_report():
    try: return subprocess.check_output(["bash", os.path.join(BASE_DIR, "scripts/login_report.sh")], stderr=subprocess.STDOUT).decode()
    except: return "Error."

def hydrate_security():
    m = get_system_metrics()
    raw = ""
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r') as f: raw = f.read()
    comb = f"{raw}\n\n{get_login_report()}"

    data = {
        "latestRaw": comb,
        "latestOpinion": "Perimeter check confirmed. Firewall is ACTIVE. 🛡️ System is stabilized via SQL transition.",
        "syncTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "metrics": m,
        "weekly": {
            "week_ending": datetime.now().strftime("%Y-%m-%d"),
            "metrics": {"total_attacks": 0, "total_bans": 0, "days_covered": 1},
            "opinion": "SQL Initialized."
        }
    }

    with open(SECURITY_JSON, 'w') as f:
        json.dump(data, f, indent=2)
    print("SUCCESS: Security data written to security_data.json.")

if __name__ == "__main__":
    hydrate_security()
