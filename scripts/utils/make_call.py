#!/usr/bin/env python3
"""
Alpha outbound call initiator.
Calls any phone number with a task for Alpha to accomplish.

Usage:
  python3 make_call.py --to "+13054441234" --task "Book a table for 2 at 8pm Saturday"

Alpha constructs --task as a free-text brief. Fully generic — works for any call type:
  restaurant bookings, contractor quotes, appointment reminders, service cancellations, etc.
"""

import argparse
import os
import sys
from pathlib import Path


def load_env():
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    os.environ.setdefault(key.strip(), value.strip())


def main():
    load_env()

    parser = argparse.ArgumentParser(
        description='Alpha outbound voice call — complete a task over the phone'
    )
    parser.add_argument(
        '--to', required=True,
        help='Target phone number in E.164 format (e.g. +13054441234)'
    )
    parser.add_argument(
        '--task', required=True,
        help=(
            'Full task brief for Alpha. Include all context needed to complete the call. '
            'Example: "Book a table for 2 at 8pm this Saturday at Nobu Miami. '
            'Preference for a window seat if available."'
        )
    )
    args = parser.parse_args()

    if not args.to.startswith('+'):
        print("✗ Phone number must be E.164 format (e.g. +13054441234)", file=sys.stderr)
        sys.exit(1)

    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_FROM_NUMBER')
    websocket_url = os.environ.get('WEBSOCKET_URL')
    caller_name = os.environ.get('CALLER_NAME', 'the user')
    callback_number = os.environ.get('CALLBACK_NUMBER', '')

    if not all([account_sid, auth_token, from_number]):
        print("✗ Missing Twilio credentials — check .env", file=sys.stderr)
        sys.exit(1)

    from twilio.rest import Client
    from twilio.twiml.voice_response import VoiceResponse, Connect, Stream

    response = VoiceResponse()
    connect = Connect()
    stream = Stream(url=websocket_url, name="alpha-outbound")
    stream.parameter(name="task", value=args.task)
    stream.parameter(name="caller_name", value=caller_name)
    stream.parameter(name="callback_number", value=callback_number)
    stream.parameter(name="mode", value="outbound")
    connect.append(stream)
    response.append(connect)

    client = Client(account_sid, auth_token)
    call = client.calls.create(
        to=args.to,
        from_=from_number,
        twiml=str(response)
    )

    print(f"✓ Call initiated")
    print(f"  SID:  {call.sid}")
    print(f"  To:   {args.to}")
    print(f"  Task: {args.task}")


if __name__ == '__main__':
    main()
