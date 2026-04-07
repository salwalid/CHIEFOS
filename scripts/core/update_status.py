import json
import os
import time
from datetime import datetime

# Path configuration
BASE_AGENTS_DIR = os.environ.get("AGENTS_DIR", "")  # Set AGENTS_DIR in .env
AGENT_PATHS = {
    "alpha": os.path.join(BASE_AGENTS_DIR, "main/sessions/"),
    "js": os.path.join(BASE_AGENTS_DIR, "js/sessions/"),
    "angel": os.path.join(BASE_AGENTS_DIR, "angel/sessions/")
}
# Fix: Using the correct live web directory
OUTPUT_PATH = os.path.join(BASE_DIR, "www/HQ/office/agent_data.json")

# Agent identity mapping (normalize keys from sessions.json)
AGENT_MAP = {
    "agent:main:main": "alpha",
    "agent:opus:subagent": "js",
    "agent:js:subagent": "js",
    "agent:main:cron": "angel",
    "agent:angel:subagent": "angel"
}

# Static/Default agent metadata
AGENT_META = {
    "alpha": {"name": "Alpha", "role": "Orchestrator", "sprite": "alpha_idle"},
    "js": {"name": "JS", "role": "Coder", "sprite": "js_idle"},
    "angel": {"name": "Angel", "role": "Guardian", "sprite": "angel_idle"},
    "super": {"name": "Agent-F", "role": "Manager", "sprite": "super_idle"},
    "agent-d": {"name": "Agent-D", "role": "Analyst", "sprite": "agent-d_idle"}
}

def parse_activity(agent_id, session_id):
    """Scan the .jsonl log for the most recent activity message."""
    session_dir = AGENT_PATHS.get(agent_id, AGENT_PATHS["alpha"])
    log_file = os.path.join(session_dir, f"{session_id}.jsonl")
    if not os.path.exists(log_file):
        return "Idle"
    
    try:
        # Read the last few lines to find activity
        with open(log_file, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            # Read last 8KB
            offset = max(0, size - 8192)
            f.seek(offset)
            lines = f.readlines()
            
            for line in reversed(lines):
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "message" and entry.get("role") == "assistant":
                        text = entry.get("content", "")
                        if text:
                            # Clean markdown and common noise
                            clean_text = text.replace("`", "").replace("#", "").strip()
                            activity = clean_text.split('\n')[0][:60]
                            return activity if activity else "Thinking..."
                except:
                    continue
    except Exception as e:
        return f"Active"
    
    return "Idle"

def get_agent_status():
    agents = {k: {"status": "Idle", "activity": "Standing by", "last_seen": 0} for k in AGENT_META.keys()}
    recent_events = []

    # Scan each agent's session directory
    for agent_id, session_dir in AGENT_PATHS.items():
        sessions_json_path = os.path.join(session_dir, "sessions.json")
        if not os.path.exists(sessions_json_path):
            continue

        try:
            with open(sessions_json_path, "r") as f:
                sessions = json.load(f)
            
            now_ms = time.time() * 1000
            
            for key, session in sessions.items():
                # Check if this session belongs to the current agent context
                matched_agent_id = None
                for pattern, aid in AGENT_MAP.items():
                    if key.startswith(pattern):
                        matched_agent_id = aid
                        break
                
                # Only process if it matches the current directory's intended agent
                if matched_agent_id != agent_id:
                    continue
                
                updated_at = session.get("updatedAt", 0)
                # Active threshold: 10 minutes
                if now_ms - updated_at < 600000:
                    agents[agent_id]["status"] = "Active"
                    agents[agent_id]["activity"] = parse_activity(agent_id, session.get("sessionId"))
                    agents[agent_id]["last_seen"] = updated_at
                    
                    # Add to recent events if very recent (last 10m)
                    if now_ms - updated_at < 600000:
                        ts = datetime.fromtimestamp(updated_at/1000).strftime("%H:%M:%S")
                        act = agents[agent_id]["activity"]
                        if act != "Idle":
                            recent_events.append(f"[{ts}] {AGENT_META[agent_id]['name']}: {act}")

        except Exception as e:
            print(f"Error parsing sessions for {agent_id}: {e}")

    # Final data assembly
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "agents": {aid: {**AGENT_META[aid], **agents[aid]} for aid in AGENT_META},
        "recent_activity": sorted(recent_events, reverse=True)[:15]
    }
    return data

if __name__ == "__main__":
    print(f"Starting update_status.py writing to {OUTPUT_PATH}")
    while True:
        try:
            status_data = get_agent_status()
            with open(OUTPUT_PATH, "w") as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            print(f"Update failed: {e}")
        time.sleep(10) # Update every 10 seconds for more "real-time" feel
