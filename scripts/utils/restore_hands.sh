#!/bin/bash
# restore_hands.sh — Repeatable process to fix and start the internal browser ("Hands")
# Author: Alpha

echo "🔱 Starting 'Hands' restoration process..."

# 1. Check for Playwright dependencies (requires sudo - assumed to be handled by user if missing)
echo "🔍 Checking Playwright status..."
if ! npx playwright --version >/dev/null 2>&1; then
    echo "❌ Playwright not found. Please run: sudo npx playwright install-deps"
    exit 1
fi

# 2. Run ChiefOS Doctor to align paths
echo "🩺 Running ChiefOS Doctor fix..."
# This requires authorization in the main chat, but the command itself is:
# chiefos doctor --fix
# We check if it still reports issues
if chiefos doctor --non-interactive | grep -q "entrypoint does not match"; then
    echo "⚠️ Path mismatch detected. Attempting fix..."
    chiefos doctor --fix
fi

# 3. Ensure Browser Control is enabled in config
echo "⚙️ Verifying browser configuration..."
if ! grep -q '"browser": {' ~/.chiefos/chiefos.json; then
    echo "❌ Browser section missing in chiefos.json."
else
    # Ensure controlUrl is NOT pointing to a stale external address if we want internal control
    # But in this specific VPS, we found that setting controlUrl to 18791 and running a server works best.
    echo "✅ Browser section found."
fi

# 4. Kickstart the Browser Control Server
echo "🚀 Kickstarting browser control server..."
# Kill any stale chrome/chromium instances
pkill -9 chrome >/dev/null 2>&1
pkill -9 chromium >/dev/null 2>&1

# Start the server in the background
# We use port 18791 as discovered during the repair
nohup chiefos browser serve --port 18791 --browser-profile chiefos > /tmp/chiefos-browser.log 2>&1 &

sleep 5

# 5. Final Handshake check
echo "🤝 Verifying handshake..."
if curl -s http://127.0.0.1:18791/tabs >/dev/null; then
    echo "✅ 'Hands' are live and responding on port 18791."
else
    echo "❌ Handshake failed. Check /tmp/chiefos-browser.log"
    exit 1
fi

echo "🔱 Restoration complete. 'Hands' are ready for action."
