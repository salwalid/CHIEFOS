import os
import json
import sqlite3
from datetime import datetime

BASE_DIR = os.environ.get("BASE_DIR", "/home/chiefos/chiefos")
PROPERTY_JSON = os.path.join(BASE_DIR, "www/HQ/property/property_data.json")
DB_PATH = os.path.join(BASE_DIR, os.environ.get("DB_NAME", "chiefos.db"))

def hydrate_properties():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM properties WHERE type NOT LIKE 'Domain' ORDER BY id")
    rows = cursor.fetchall()
    conn.close()

    assets = {row['id']: dict(row) for row in rows}

    data = {
        "assets": assets,
        "syncTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(PROPERTY_JSON, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"SUCCESS: property_data.json written ({len(assets)} properties).")

if __name__ == "__main__":
    hydrate_properties()
