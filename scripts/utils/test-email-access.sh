#!/bin/bash
# test-email-access.sh - Verify email credentials and IMAP/SMTP access

set -euo pipefail

echo "🔐 Testing Alpha Email Access"
echo "Email: ${GMAIL_USER}"
echo ""

# Test IMAP (reading emails)
echo "📥 Testing IMAP (read access)..."
timeout 10 curl --url "imaps://imap.gmail.com:993" \
  --user "${GMAIL_USER}:${GMAIL_PASS}" \
  --request "EXAMINE INBOX" \
  2>&1 | grep -q "OK" && echo "✅ IMAP connection successful" || echo "❌ IMAP connection failed"

echo ""

# Test SMTP (sending emails)  
echo "📤 Testing SMTP (send access)..."
timeout 10 curl --url "smtp://smtp.gmail.com:587" \
  --mail-from "${GMAIL_USER}" \
  --mail-rcpt "${GMAIL_USER}" \
  --user "${GMAIL_USER}:${GMAIL_PASS}" \
  --ssl-reqd \
  2>&1 | grep -q "220" && echo "✅ SMTP connection successful" || echo "❌ SMTP connection failed"

echo ""
echo "✅ Email access test complete"
