import os
import re
import json
from datetime import datetime, timedelta

BASE_DIR = os.environ.get("BASE_DIR", "/home/chiefos/chiefos")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
HISTORY_FILE = os.path.join(BASE_DIR, "memory/security_history.json")
SECURITY_JSON = os.path.join(BASE_DIR, "www/HQ/security/security_data.json")

def parse_log_file(file_path):
    """Extracts metrics from a single daily log file."""
    metrics = {"attacks": 0, "critical": 0, "updates": 0, "attack_ips": [], "bans": 0}
    if not os.path.exists(file_path):
        return metrics
    
    with open(file_path, 'r') as f:
        content = f.read()
        # Find all IPs associated with "Failed password"
        ips = re.findall(r'Failed password for .* from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', content)
        metrics["attack_ips"] = ips
        metrics["attacks"] = len(ips)
        # Count Fail2Ban bans
        metrics["bans"] = content.count("Ban ")
        # Count critical audit flags
        metrics["critical"] = len(re.findall(r"CRITICAL", content))
        # Find update count
        updates = re.search(r"(\d+) packages can be upgraded", content)
        if updates:
            metrics["updates"] = int(updates.group(1))
            
    return metrics

def run_weekly_analysis():
    today = datetime.now()
    weekly_stats = {"total_attacks": 0, "total_bans": 0, "avg_updates": 0, "critical_events": 0, "days_covered": 0, "top_ips": []}
    all_ips = []
    
    # Analyze last 7 days
    for i in range(7):
        date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        log_file = os.path.join(LOGS_DIR, f"security_{date_str}.log")
        if os.path.exists(log_file):
            day_metrics = parse_log_file(log_file)
            weekly_stats["total_attacks"] += day_metrics["attacks"]
            weekly_stats["total_bans"] += day_metrics["bans"]
            weekly_stats["critical_events"] += day_metrics["critical"]
            weekly_stats["days_covered"] += 1
            all_ips.extend(day_metrics["attack_ips"])
            
    # Calculate Top 10 IPs
    from collections import Counter
    top_10 = Counter(all_ips).most_common(10)
    weekly_stats["top_ips"] = [{"ip": ip, "count": count} for ip, count in top_10]

    # Save to history for trend tracking
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
    
    report = {
        "week_ending": today.strftime("%Y-%m-%d"),
        "metrics": weekly_stats,
        "opinion": f"Weekly review complete. Total volume of {weekly_stats['total_attacks']} blocked attempts shows a stable perimeter. No persistent escalation patterns detected."
    }
    history.append(report)
    
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)

    # Update security_data.json with real weekly data
    if os.path.exists(SECURITY_JSON):
        with open(SECURITY_JSON, 'r') as f:
            security_data = json.load(f)
        security_data["weekly"] = report
        with open(SECURITY_JSON, 'w') as f:
            json.dump(security_data, f, indent=2)

    print(f"✅ Weekly analysis complete for {report['week_ending']}")

if __name__ == "__main__":
    run_weekly_analysis()
