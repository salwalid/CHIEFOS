#!/usr/bin/env python3
"""
Direct Twilio Call Script
Makes a phone call using Twilio with TTS message delivery.
"""

import argparse
import sys
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

# Twilio credentials
TWILIO_ACCOUNT_SID = "REDACTED_TWILIO_ACCOUNT_SID"
TWILIO_AUTH_TOKEN = "REDACTED_TWILIO_AUTH_TOKEN"
TWILIO_FROM_NUMBER = "REDACTED_TWILIO_FROM_NUMBER"


def generate_twiml(message):
    """Generate TwiML with the message using Amazon Polly Joanna voice."""
    response = VoiceResponse()
    response.say(
        message,
        voice="Polly.Joanna",
        language="en-US"
    )
    return str(response)


def make_call(to_number, message):
    """Initiate a phone call with the given message."""
    try:
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Generate TwiML
        twiml = generate_twiml(message)
        
        # Make the call
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_FROM_NUMBER,
            twiml=twiml
        )
        
        print(f"✓ Call initiated successfully!")
        print(f"  Call SID: {call.sid}")
        print(f"  To: {to_number}")
        print(f"  From: {TWILIO_FROM_NUMBER}")
        print(f"  Status: {call.status}")
        print(f"  Message: {message}")
        
        return call.sid
        
    except Exception as e:
        print(f"✗ Error making call: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Make a phone call using Twilio with TTS message"
    )
    parser.add_argument(
        "--to",
        required=True,
        help="Destination phone number (E.164 format, e.g., +15551234567)"
    )
    parser.add_argument(
        "--message",
        required=True,
        help="Message to speak during the call"
    )
    
    args = parser.parse_args()
    
    # Validate phone number format
    if not args.to.startswith('+'):
        print("✗ Error: Phone number must be in E.164 format (start with +)", file=sys.stderr)
        sys.exit(1)
    
    # Make the call
    make_call(args.to, args.message)


if __name__ == "__main__":
    main()
