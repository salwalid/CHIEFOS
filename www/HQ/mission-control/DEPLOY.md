# Mission Control — Deployment Guide

## Quick Deploy (5 minutes)

### Step 1: Upload to VPS
```bash
# From your local machine, SCP the entire folder:
scp -r mission-control/ root@your-vps:/var/www/chiefos.example.com/

# OR if you're already on the VPS, just copy it:
cp -r mission-control/ /var/www/chiefos.example.com/
```

Adjust the path to wherever your chiefos.example.com web root is.

### Step 2: Install PyYAML (if not already installed)
```bash
pip3 install pyyaml
```

### Step 3: Run the build script
```bash
cd /var/www/chiefos.example.com/mission-control
chmod +x build.sh
./build.sh
```

You should see:
```
✅ Built .../data/mission-control.json
   7 agents, 6 schedules
```

### Step 4: Open in browser
```
https://chiefos.example.com/mission-control/team.html
https://chiefos.example.com/mission-control/calendar.html
https://chiefos.example.com/mission-control/office.html
```

That's it. You're live.

---

## File Structure
```
mission-control/
├── agents/                    ← One YAML per agent (edit these)
│   ├── alpha.yaml             ← Alpha (Chief of Staff)
│   ├── angel.yaml             ← The Angel (Guardian)
│   ├── chatty.yaml            ← Chatty (GPT-4o)
│   ├── gemini-flash.yaml      ← Gemi (Gemini Flash)
│   ├── json.yaml              ← JSON (Coding Specialist)
│   ├── opus.yaml              ← Antho (Claude Opus)
│   └── sonnet.yaml            ← Sonnet (Claude Sonnet)
├── schedules/
│   └── schedules.yaml         ← All cron jobs and scheduled tasks
├── data/
│   └── mission-control.json   ← AUTO-GENERATED — do not edit
├── build.sh                   ← Compiles YAML → JSON
├── team.html                  ← Screen 1: Org Chart
├── calendar.html              ← Screen 2: Schedule Timeline
├── office.html                ← Screen 3: Pixel Art Office
└── DEPLOY.md                  ← This file
```

---

## How to Add a New Agent

1. Create a YAML file in `agents/`:
```bash
nano agents/new-agent.yaml
```

2. Use this template:
```yaml
id: my-agent-id          # Must match chiefos.json agent id
name: Display Name
role: What it does
emoji: "🤖"
model: provider/model-name
status: active            # or on-demand
tier: specialist          # orchestrator | guardian | specialist
reports_to: main          # who it reports to
workspace: $CHIEFOS_HOME
capabilities:
  - Capability one
  - Capability two
channels: []
notes: >
  Any additional context.
```

3. Rebuild:
```bash
./build.sh
```

4. Refresh browser. Done.

## How to Update Schedules

Edit `schedules/schedules.yaml` — add or modify entries, then run `./build.sh`.

## How to Auto-Rebuild on Change (Optional)

Add to your crontab to rebuild every 5 minutes:
```bash
*/5 * * * * cd /var/www/chiefos.example.com/mission-control && ./build.sh >> /dev/null 2>&1
```

Or use inotifywait for instant rebuilds:
```bash
while inotifywait -r -e modify agents/ schedules/; do ./build.sh; done &
```
