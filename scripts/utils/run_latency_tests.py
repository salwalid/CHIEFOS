import time
import requests
import sqlite3
import os
import subprocess
from datetime import datetime

# DB Config
DB_PATH = os.path.join(os.environ.get("BASE_DIR", "/home/chiefos/chiefos"), os.environ.get("DB_NAME", "chiefos.db"))
ANGEL_URL = f"http://127.0.0.1:{os.environ.get('ANGEL_PORT', '39571')}/mcp"

def record_test(test_id, test_case, tier, mode, total_time_ms, guardian_time_ms, est_tokens):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO table_Latency_Tests (test_id, test_case, tier, mode, total_time_ms, guardian_time_ms, est_tokens, cost_usd) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                   (test_id, test_case, tier, mode, int(total_time_ms), int(guardian_time_ms), est_tokens, (est_tokens / 1000000.0) * 0.15)) 
    conn.commit()
    conn.close()

def run_guardian(action, auth='NONE', msg='NONE', transcript='NONE'):
    start = time.time()
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "verify_action_plan",
            "arguments": {
                "action": action,
                "auth": auth,
                "msg": msg,
                "transcript_snapshot": transcript
            }
        },
        "id": 1
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    try:
        resp = requests.post(ANGEL_URL, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"Guardian error: {e}")
    return (time.time() - start) * 1000

# Test 1: Baseline (Get Time)
def test_1():
    test_id = 'T1'
    test_case = 'Get Current Time'
    tier = 1
    action = "Get the current time using the date command."

    # With Guardian
    start_total = time.time()
    g_time = run_guardian(action)
    subprocess.run(['date'], capture_output=True)
    total_time = (time.time() - start_total) * 1000
    record_test(test_id, test_case, tier, 'With', total_time, g_time, 400)

    # Without Guardian
    start_total = time.time()
    subprocess.run(['date'], capture_output=True)
    total_time = (time.time() - start_total) * 1000
    record_test(test_id, test_case, tier, 'Without', total_time, 0, 0)

# Test 2: Research (List files)
def test_2():
    test_id = 'T2'
    test_case = 'List files in root'
    tier = 1
    action = "List the files in the root directory for research."

    # With Guardian
    start_total = time.time()
    g_time = run_guardian(action)
    subprocess.run(['ls', '-F'], capture_output=True)
    total_time = (time.time() - start_total) * 1000
    record_test(test_id, test_case, tier, 'With', total_time, g_time, 420)

    # Without Guardian
    start_total = time.time()
    subprocess.run(['ls', '-F'], capture_output=True)
    total_time = (time.time() - start_total) * 1000
    record_test(test_id, test_case, tier, 'Without', total_time, 0, 0)

# Test 3: Additive (Insert into DB)
def test_3():
    test_id = 'T3'
    test_case = 'Insert Latency Baseline'
    tier = 2
    action = "Insert 'latency_baseline_marker' into table_Alpha_Intel."

    # With Guardian
    start_total = time.time()
    g_time = run_guardian(action)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO table_Alpha_Intel (key, value) VALUES (?, ?)', ('latency_baseline', '2026-03-26'))
    conn.commit()
    conn.close()
    total_time = (time.time() - start_total) * 1000
    record_test(test_id, test_case, tier, 'With', total_time, g_time, 450)

    # Without Guardian
    start_total = time.time()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO table_Alpha_Intel (key, value) VALUES (?, ?)', ('latency_baseline_no_g', '2026-03-26'))
    conn.commit()
    conn.close()
    total_time = (time.time() - start_total) * 1000
    record_test(test_id, test_case, tier, 'Without', total_time, 0, 0)

# Test 4: Operate (Update status)
def test_4():
    test_id = 'T4'
    test_case = 'Update status in Alpha_Intel'
    tier = 3
    action = "Update the value of 'latency_baseline' in table_Alpha_Intel."

    # With Guardian
    start_total = time.time()
    g_time = run_guardian(action)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE table_Alpha_Intel SET value = ? WHERE key = ?', ('updated_2026', 'latency_baseline'))
    conn.commit()
    conn.close()
    total_time = (time.time() - start_total) * 1000
    record_test(test_id, test_case, tier, 'With', total_time, g_time, 480)

    # Without Guardian
    start_total = time.time()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE table_Alpha_Intel SET value = ? WHERE key = ?', ('updated_2026_no_g', 'latency_baseline_no_g'))
    conn.commit()
    conn.close()
    total_time = (time.time() - start_total) * 1000
    record_test(test_id, test_case, tier, 'Without', total_time, 0, 0)

# Test 5: Consequential (Delete temp file)
def test_5():
    test_id = 'T5'
    test_case = 'Delete Temporary File'
    tier = 4
    action = "Delete the temporary file 'latency_temp_file.tmp' to verify authorization loop."
    auth_phrase = "I authorize you to suspend the Guardian protocol for the MaatSpec Latency & Cost Test Suite"
    with open('latency_temp_file.tmp', 'a'): os.utime('latency_temp_file.tmp', None)

    # With Guardian
    start_total = time.time()
    g_time = run_guardian(action, auth=auth_phrase, msg='5791')
    os.remove('latency_temp_file.tmp')
    total_time = (time.time() - start_total) * 1000
    record_test(test_id, test_case, tier, 'With', total_time, g_time, 600)

    # Without Guardian
    with open('latency_temp_file_no_g.tmp', 'a'): os.utime('latency_temp_file_no_g.tmp', None)
    start_total = time.time()
    os.remove('latency_temp_file_no_g.tmp')
    total_time = (time.time() - start_total) * 1000
    record_test(test_id, test_case, tier, 'Without', total_time, 0, 0)

if __name__ == '__main__':
    print("🚀 Starting Latency Tests...")
    test_1(); print("✅ Test 1 Complete")
    test_2(); print("✅ Test 2 Complete")
    test_3(); print("✅ Test 3 Complete")
    test_4(); print("✅ Test 4 Complete")
    test_5(); print("✅ Test 5 Complete")
    print("📊 All tests finished. Results recorded in table_Latency_Tests.")
