import sqlite3
import subprocess
import csv
import io
import os

# Path to the XLSX file
xlsx_path = os.environ.get("BLUEPRINT_XLSX_PATH", "")  # Set BLUEPRINT_XLSX_PATH in .env to your Excel file path
db_path = os.path.join(os.environ.get("BASE_DIR", "/home/chiefos/chiefos"), os.environ.get("DB_NAME", "chiefos.db"))

def get_focus_type(activity):
    a = activity.lower()
    if any(x in a for x in ["gym", "stretch", "walk", "exercise", "coffee"]):
        return "Health / Recovery"
    if any(x in a for x in ["washroom", "teeth", "shower", "routine", "lunch", "dinner"]):
        return "Ritual / Administrative"
    if any(x in a for x in ["linkedin", "blog", "app /"]):
        return "Creative / Content"
    if any(x in a for x in ["main work", "dba", "meeting", "lecture"]):
        return "High Focus"
    if "commute" in a:
        return "Transition"
    if any(x in a for x in ["app work", "study", "reno", "org"]):
        return "Development"
    if "sleep" in a:
        return "Rest"
    return "Neutral"

def get_alpha_protocol(focus):
    if focus in ["Health / Recovery", "Rest", "Ritual / Administrative"]:
        return "Silent"
    if focus == "Creative / Content":
        return "Drafting Mode"
    if focus in ["High Focus", "Development"]:
        return "Focus Mode (Alerts Only)"
    if focus == "Transition":
        return "Voice Briefing"
    return "Monitoring"

# 1. Convert XLSX to CSV using npx xlsx-cli
try:
    result = subprocess.run(["npx", "xlsx-cli", xlsx_path], capture_output=True, text=True, check=True)
    csv_content = result.stdout
except Exception as e:
    print(f"Error converting XLSX: {e}")
    exit(1)

# 2. Parse CSV
reader = csv.reader(io.StringIO(csv_content))
header = next(reader)
days = header[1:] # Monday through Sunday

# Store rows: {Time: [Mon_Act, Tue_Act, ...]}
schedule_data = []
for row in reader:
    if not row or not row[0]: continue
    time = row[0]
    acts = row[1:]
    schedule_data.append({"time": time, "acts": acts})

# 3. Connect to DB and Insert
conn = sqlite3.connect(db_path)
curr = conn.cursor()

# Clear existing entries if any (Safe during initial population)
curr.execute("DELETE FROM table_principle_week_blueprint;")

for day_idx, day_name in enumerate(days):
    for i, row in enumerate(schedule_data):
        time = row['time']
        activity = row['acts'][day_idx] if day_idx < len(row['acts']) else ""
        
        if not activity or activity.strip() == "":
            continue
            
        # Determine end_time from next row or logical increment
        if i + 1 < len(schedule_data):
            end_time = schedule_data[i+1]['time']
        else:
            # Handle the last row (usually Sleep Time)
            end_time = "05:00" # Cycle back or end of day
            
        focus = get_focus_type(activity)
        protocol = get_alpha_protocol(focus)
        
        curr.execute("""
            INSERT INTO table_principle_week_blueprint 
            (day_of_week, start_time, end_time, activity_name, focus_type, alpha_protocol)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (day_name.split(' ')[0], time, end_time, activity, focus, protocol))

conn.commit()
conn.close()
print("Successfully populated table_principle_week_blueprint.")
