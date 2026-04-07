import sqlite3
import os
from datetime import datetime

db_path = os.path.join(os.environ.get("BASE_DIR", "/home/chiefos/chiefos"), os.environ.get("DB_NAME", "chiefos.db"))
output_path = os.path.join(BASE_DIR, "www/HQ/weekly_layout/index.html")

def parse_time(t_str):
    try:
        return datetime.strptime(t_str, "%H:%M")
    except:
        return datetime.strptime("00:00", "%H:%M")

def get_color_class(activity):
    if not activity: return "empty"
    a = activity.lower()
    if any(x in a for x in ["gym", "stretch", "exercise"]):
        return "health"
    if any(x in a for x in ["washroom", "teeth", "shower", "routine", "lunch", "dinner", "walk"]):
        return "ritual"
    if any(x in a for x in ["linkedin", "blog", "app /", "app work"]):
        return "creative"
    if any(x in a for x in ["main work", "dba", "meeting", "lecture", "study"]):
        return "work"
    if any(x in a for x in ["commute", "daycare", "pickup"]):
        return "transition"
    if any(x in a for x in ["reno", "org"]):
        return "property"
    if "sleep" in a:
        return "rest"
    if "coffe" in a:
        return "social"
    return ""

def generate_html():
    conn = sqlite3.connect(db_path)
    curr = conn.cursor()
    
    curr.execute("SELECT day_of_week, start_time, activity_name FROM table_principle_week_blueprint;")
    rows = curr.fetchall()
    
    data = {}
    unique_times = set()
    for day, time, act in rows:
        if day not in data: data[day] = {}
        data[day][time] = act
        unique_times.add(time)
    
    conn.close()

    sorted_times = sorted(list(unique_times), key=parse_time)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    time_rows = []
    for time in sorted_times:
        cells = [f'<div class="time-slot">{time}</div>']
        for day in days:
            act = data.get(day, {}).get(time, "")
            cls = get_color_class(act)
            cells.append(f'<div class="cell {cls}">{act}</div>')
        time_rows.append("".join(cells))

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weekly Rhythm | ChiefOS HQ</title>
        <style>
            :root {{
                --bg: #0a0b0d;
                --surface: #14161a;
                --border: #2d3139;
                --accent: #3b82f6;
                --text: #e2e8f0;
                --text-dim: #94a3b8;
                
                /* Category Colors */
                --c-health: #059669;
                --c-ritual: #475569;
                --c-creative: #7c3aed;
                --c-work: #2563eb;
                --c-transition: #d97706;
                --c-property: #db2777;
                --c-rest: #1e293b;
                --c-social: #dc2626;
            }}
            body {{
                background: var(--bg);
                color: var(--text);
                font-family: 'Inter', system-ui, sans-serif;
                margin: 0;
                padding: 40px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            h1 {{
                font-size: 2rem;
                letter-spacing: -0.025em;
                margin-bottom: 40px;
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            .trident {{ color: var(--accent); }}
            .grid {{
                display: grid;
                grid-template-columns: 100px repeat(7, 1fr);
                gap: 1px;
                background: var(--border);
                border: 1px solid var(--border);
                border-radius: 12px;
                overflow: hidden;
                width: 100%;
                max-width: 1400px;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
            }}
            .header {{
                background: var(--surface);
                padding: 16px;
                font-weight: 600;
                text-align: center;
                font-size: 0.875rem;
                color: var(--text-dim);
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            .time-slot {{
                background: var(--surface);
                padding: 12px;
                font-size: 0.75rem;
                font-family: monospace;
                color: var(--text-dim);
                display: flex;
                align-items: center;
                justify-content: center;
                border-right: 1px solid var(--border);
            }}
            .cell {{
                background: var(--bg);
                padding: 12px;
                font-size: 0.8125rem;
                min-height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                transition: opacity 0.2s;
                color: #ffffff;
                font-weight: 500;
            }}
            .cell:hover {{
                opacity: 0.8;
            }}
            .cell.empty {{ color: transparent; background: var(--bg); }}
            
            /* Category Assignments */
            .health {{ background: var(--c-health); }}
            .ritual {{ background: var(--c-ritual); }}
            .creative {{ background: var(--c-creative); }}
            .work {{ background: var(--c-work); }}
            .transition {{ background: var(--c-transition); }}
            .property {{ background: var(--c-property); }}
            .rest {{ background: var(--c-rest); color: var(--text-dim); }}
            .social {{ background: var(--c-social); }}
        </style>
    </head>
    <body>
        <h1><span class="trident">🔱</span> Master Weekly Rhythm</h1>
        <div class="grid">
            <div class="header">Time</div>
            {"".join(f'<div class="header">{{day}}</div>' for day in days).format(**{"day": ""})}
            {"".join(time_rows)}
        </div>
    </body>
    </html>
    """
    
    with open(output_path, "w") as f:
        f.write(html)
    print(f"Weekly Layout with color-coding hydrated at {output_path}")

if __name__ == "__main__":
    generate_html()
