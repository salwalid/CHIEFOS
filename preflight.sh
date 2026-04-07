#!/usr/bin/env bash
# =============================================================
# ChiefOS Preflight Check
# Audits the target machine before install begins.
# Exits 0 if ready, exits 1 if any blockers found.
# =============================================================

set -euo pipefail

PASS="✅"
WARN="⚠️ "
FAIL="❌"
BLOCKERS=0
WARNINGS=0

# Load config if present
CONFIG_FILE="$(dirname "$0")/config.env"
if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
else
    echo "${WARN} config.env not found — copy config.env.template and fill it in first."
    echo "    cp config.env.template config.env"
    exit 1
fi

ANGEL_PORT="${ANGEL_PORT:-39571}"
MIN_DISK_MB=500

echo ""
echo "=============================="
echo "  ChiefOS Preflight Check"
echo "=============================="
echo ""

# --- OS Info ---
OS_INFO=$(lsb_release -ds 2>/dev/null || cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2 | tr -d '"' || echo "Unknown OS")
echo "${PASS} OS: $OS_INFO"

# --- Disk space ---
FREE_MB=$(df -m "$HOME" | awk 'NR==2 {print $4}')
if [[ "$FREE_MB" -ge "$MIN_DISK_MB" ]]; then
    echo "${PASS} Disk space: ${FREE_MB}MB free"
else
    echo "${FAIL} Disk space: ${FREE_MB}MB free — minimum ${MIN_DISK_MB}MB required"
    BLOCKERS=$((BLOCKERS + 1))
fi

# --- Python 3 ---
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [[ "$PY_MAJOR" -ge 3 && "$PY_MINOR" -ge 8 ]]; then
        echo "${PASS} Python $PY_VER"
    else
        echo "${FAIL} Python $PY_VER — minimum 3.8 required"
        BLOCKERS=$((BLOCKERS + 1))
    fi
else
    echo "${FAIL} Python 3 not found"
    BLOCKERS=$((BLOCKERS + 1))
fi

# --- SQLite3 ---
if command -v sqlite3 &>/dev/null; then
    echo "${PASS} SQLite3 $(sqlite3 --version | awk '{print $1}')"
else
    echo "${FAIL} SQLite3 not found — install with: sudo apt install sqlite3"
    BLOCKERS=$((BLOCKERS + 1))
fi

# --- Node.js ---
if command -v node &>/dev/null; then
    NODE_VER=$(node --version | tr -d 'v')
    NODE_MAJOR=$(echo "$NODE_VER" | cut -d. -f1)
    if [[ "$NODE_MAJOR" -ge 18 ]]; then
        echo "${PASS} Node.js v$NODE_VER"
    else
        echo "${FAIL} Node.js v$NODE_VER — minimum v18 required"
        BLOCKERS=$((BLOCKERS + 1))
    fi
else
    echo "${FAIL} Node.js not found — install v18+ from https://nodejs.org"
    BLOCKERS=$((BLOCKERS + 1))
fi

# --- npm ---
if command -v npm &>/dev/null; then
    echo "${PASS} npm $(npm --version)"
else
    echo "${FAIL} npm not found"
    BLOCKERS=$((BLOCKERS + 1))
fi

# --- PM2 ---
if command -v pm2 &>/dev/null; then
    echo "${PASS} PM2 $(pm2 --version)"
else
    echo "${WARN} PM2 not found — will be installed automatically (npm install -g pm2)"
    WARNINGS=$((WARNINGS + 1))
fi

# --- Git ---
if command -v git &>/dev/null; then
    echo "${PASS} Git $(git --version | awk '{print $3}')"
else
    echo "${FAIL} Git not found — install with: sudo apt install git"
    BLOCKERS=$((BLOCKERS + 1))
fi

# --- Cron ---
if command -v crontab &>/dev/null; then
    echo "${PASS} cron available"
else
    echo "${FAIL} cron not found — install with: sudo apt install cron"
    BLOCKERS=$((BLOCKERS + 1))
fi

# --- curl ---
if command -v curl &>/dev/null; then
    echo "${PASS} curl available"
else
    echo "${FAIL} curl not found — install with: sudo apt install curl"
    BLOCKERS=$((BLOCKERS + 1))
fi

# --- sudo access ---
if sudo -n true 2>/dev/null; then
    echo "${PASS} sudo access confirmed"
else
    echo "${FAIL} sudo access required (Angel must run as a separate OS user)"
    BLOCKERS=$((BLOCKERS + 1))
fi

# --- Angel port availability ---
if command -v ss &>/dev/null; then
    if ss -ltn 2>/dev/null | grep -q ":${ANGEL_PORT}"; then
        echo "${FAIL} Port ${ANGEL_PORT} is already in use — change ANGEL_PORT in config.env"
        BLOCKERS=$((BLOCKERS + 1))
    else
        echo "${PASS} Port ${ANGEL_PORT} available for Angel"
    fi
else
    echo "${WARN} Could not check port ${ANGEL_PORT} (ss not available)"
    WARNINGS=$((WARNINGS + 1))
fi

# --- Internet connectivity ---
if curl -sf --max-time 5 https://github.com > /dev/null 2>&1; then
    echo "${PASS} Internet connectivity confirmed"
else
    echo "${FAIL} Cannot reach GitHub — internet connection required"
    BLOCKERS=$((BLOCKERS + 1))
fi

# --- OpenClaw detection ---
echo ""
echo "--- Environment Detection ---"
if [[ -f "${BASE_DIR}/SOUL.md" ]] || [[ -f "${HOME}/clawd/SOUL.md" ]]; then
    OPENCLAW_PATH="${BASE_DIR}"
    [[ -f "${HOME}/clawd/SOUL.md" ]] && OPENCLAW_PATH="${HOME}/clawd"
    echo "${WARN} Existing OpenClaw workspace detected at ${OPENCLAW_PATH}"
    echo "     → Will be updated (not replaced). Backups created before any changes."
    WARNINGS=$((WARNINGS + 1))
else
    echo "${PASS} No existing OpenClaw workspace — fresh install"
fi

# --- Existing Angel detection ---
if [[ -d "/home/angel/angel" ]]; then
    echo "${WARN} Existing Angel installation detected at /home/angel/angel"
    echo "     → Will skip Angel install. Verify she is running before proceeding."
    WARNINGS=$((WARNINGS + 1))
else
    echo "${PASS} No existing Angel installation — will install fresh"
fi

# --- Existing ChiefOS detection ---
if [[ -d "${BASE_DIR}/scripts" ]]; then
    echo "${WARN} Existing ChiefOS detected at ${BASE_DIR} — this is a re-install"
    WARNINGS=$((WARNINGS + 1))
else
    echo "${PASS} No existing ChiefOS — clean install"
fi

# --- Summary ---
echo ""
echo "=============================="
echo "  Preflight Summary"
echo "=============================="
if [[ "$BLOCKERS" -eq 0 ]]; then
    echo "${PASS} All checks passed — ${WARNINGS} warning(s)"
    echo ""
    echo "Ready to install. Run: bash install.sh"
    echo ""
    exit 0
else
    echo "${FAIL} ${BLOCKERS} blocker(s) found — fix before running install.sh"
    [[ "$WARNINGS" -gt 0 ]] && echo "${WARN} ${WARNINGS} warning(s) noted"
    echo ""
    exit 1
fi
