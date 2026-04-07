#!/bin/bash
# make-call.sh - Make a Twilio call with text-to-speech

set -euo pipefail

TO_NUMBER="$1"
MESSAGE="$2"

ACCOUNT_SID="${TWILIO_ACCOUNT_SID}"
AUTH_TOKEN="${TWILIO_AUTH_TOKEN}"
FROM_NUMBER="${TWILIO_FROM_NUMBER}"

# URL encode the message for TwiML
MESSAGE_ENCODED=$(echo "$MESSAGE" | jq -sRr @uri)

# Create TwiML with Polly.Joanna voice (natural, professional)
TWIML="<Response><Say voice=\"Polly.Joanna\">$MESSAGE</Say></Response>"
TWIML_ENCODED=$(echo "$TWIML" | jq -sRr @uri)

echo "📞 Initiating call to $TO_NUMBER..."
echo ""

# Make the call
RESPONSE=$(curl -X POST "https://api.twilio.com/2010-04-01/Accounts/$ACCOUNT_SID/Calls.json" \
  --data-urlencode "Twiml=$TWIML" \
  --data-urlencode "To=$TO_NUMBER" \
  --data-urlencode "From=$FROM_NUMBER" \
  -u "$ACCOUNT_SID:$AUTH_TOKEN" 2>&1)

# Extract Call SID
CALL_SID=$(echo "$RESPONSE" | grep -o '"sid": "[^"]*"' | head -1 | cut -d'"' -f4)

if [ -n "$CALL_SID" ]; then
    echo "✅ Call initiated successfully!"
    echo "Call SID: $CALL_SID"
    echo "From: $FROM_NUMBER"
    echo "To: $TO_NUMBER"
    echo ""
    echo "You should receive the call in a few seconds..."
else
    echo "❌ Call failed!"
    echo "$RESPONSE"
    exit 1
fi
