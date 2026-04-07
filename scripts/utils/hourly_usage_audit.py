import json
from datetime import datetime
import collections
import os

transcript_path = os.environ.get('AGENT_SESSION_PATH', '')  # Set AGENT_SESSION_PATH in .env
target_date = '2026-03-18'

PRICING = {
    'gemini-3-flash-preview': {'in': 0.10, 'out': 0.40},
    'claude-sonnet-4-5': {'in': 3.00, 'out': 15.00},
    'claude-opus-4-5': {'in': 15.00, 'out': 75.00},
    'gemini-3.1-pro-preview': {'in': 1.25, 'out': 5.00}
}

hourly = collections.defaultdict(lambda: {'in': 0, 'out': 0, 'cost': 0.0, 'count': 0, 'context': 0, 'models': set()})

if os.path.exists(transcript_path):
    with open(transcript_path, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                ts = data.get('timestamp')
                if not ts: continue
                
                if isinstance(ts, str):
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromtimestamp(ts / 1000.0)
                
                if dt.strftime('%Y-%m-%d') != target_date: continue
                
                # Check top-level or nested usage
                usage = data.get('usage') or data.get('message', {}).get('usage')
                if usage:
                    model = data.get('model') or data.get('message', {}).get('model', 'unknown')
                    m_name = model.split('/')[-1]
                    
                    in_t = usage.get('input', 0)
                    out_t = usage.get('output', 0)
                    
                    p = PRICING.get(m_name, {'in': 0.1, 'out': 0.4})
                    cost = (in_t/1000000.0)*p['in'] + (out_t/1000000.0)*p['out']
                    
                    h = dt.hour
                    hourly[h]['in'] += in_t
                    hourly[h]['out'] += out_t
                    hourly[h]['cost'] += cost
                    hourly[h]['count'] += 1
                    hourly[h]['context'] = in_t
                    hourly[h]['models'].add(m_name)
            except: continue

print("HOUR | MSGS | MODELS | IN TOKENS | OUT TOKENS | CONTEXT | COST ($)")
print("-----|------|--------|-----------|------------|---------|---------")
total_cost = 0
for h in sorted(hourly.keys()):
    s = hourly[h]
    total_cost += s['cost']
    print(f"{h:02}:00 | {s['count']:4} | {','.join(s['models']):6} | {s['in']:9,d} | {s['out']:10,d} | {s['context']:7,d} | {s['cost']:7.4f}")
print(f"TOTAL TODAY: ${total_cost:.2f}")
