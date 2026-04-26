#!/bin/bash
# Setup script for Interactive Twilio Call system

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Interactive Twilio Call - Setup"
echo "=========================================="
echo ""

# Check Python version
echo "[1/6] Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "Error: Python 3 is required"
    exit 1
fi
echo "✓ Python 3 found"
echo ""

# Check pip
echo "[2/6] Checking pip..."
python3 -m pip --version
if [ $? -ne 0 ]; then
    echo "Error: pip is required"
    exit 1
fi
echo "✓ pip found"
echo ""

# Install dependencies
echo "[3/6] Installing dependencies..."
pip3 install -r requirements_interactive.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi
echo "✓ Dependencies installed"
echo ""

# Check for .env file
echo "[4/6] Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠ No .env file found"
    echo "  Creating from example.env..."
    cp example.env .env
    echo "  Please edit .env and add your API keys:"
    echo "  - OPENAI_API_KEY (required for Whisper)"
    echo "  - ANTHROPIC_API_KEY (required for Claude)"
    echo "  - AWS credentials (required for Polly)"
    echo "  - WEBSOCKET_URL (update with your VPS IP)"
    echo ""
    echo "  Then run this script again."
    exit 0
else
    echo "✓ .env file found"
    # Load environment
    export $(cat .env | grep -v '^#' | xargs)
fi
echo ""

# Verify API keys
echo "[5/6] Verifying API keys..."
missing_keys=0

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-..." ]; then
    echo "⚠ OPENAI_API_KEY not set"
    missing_keys=1
fi

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "sk-ant-..." ]; then
    echo "⚠ ANTHROPIC_API_KEY not set"
    missing_keys=1
fi

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ "$AWS_ACCESS_KEY_ID" = "AKIA..." ]; then
    echo "⚠ AWS_ACCESS_KEY_ID not set"
    missing_keys=1
fi

if [ -z "$WEBSOCKET_URL" ] || [[ "$WEBSOCKET_URL" == *"YOUR_VPS_IP"* ]]; then
    echo "⚠ WEBSOCKET_URL not configured"
    missing_keys=1
fi

if [ $missing_keys -eq 1 ]; then
    echo ""
    echo "Please update .env with your actual API keys and VPS IP"
    exit 1
fi

echo "✓ API keys configured"
echo ""

# Test audio utilities
echo "[6/6] Testing audio utilities..."
python3 test_audio_utils.py
if [ $? -ne 0 ]; then
    echo "Error: Audio utilities test failed"
    exit 1
fi
echo ""

echo "=========================================="
echo "✓ Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start the WebSocket server:"
echo "   python3 conversation_server.py"
echo ""
echo "2. In another terminal, make a test call:"
echo "   python3 interactive_call.py --to +15551234567"
echo ""
echo "3. Or run in background with screen:"
echo "   screen -S conversation -dm python3 conversation_server.py"
echo "   screen -r conversation  # to attach"
echo ""
echo "See INTERACTIVE_CALL_README.md for full documentation"
echo ""
