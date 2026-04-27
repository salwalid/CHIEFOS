#!/usr/bin/env python3
"""
Interactive Twilio Call Script
Initiates a phone call that connects to a WebSocket server for interactive conversation.
"""

import argparse
import sys
import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

# WebSocket server configuration
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", "wss://your-vps-ip:18793/media-stream")


def generate_interactive_twiml(initial_message=None, context=None):
    """
    Generate TwiML that connects to WebSocket server for interactive conversation.
    
    Args:
        initial_message: Optional greeting message before connecting
        context: Optional context to pass to the server
    
    Returns:
        TwiML string
    """
    response = VoiceResponse()
    
    # Optional initial greeting
    if initial_message:
        response.say(
            initial_message,
            voice="Polly.Joanna",
            language="en-US"
        )
    
    # Connect to WebSocket stream
    connect = Connect()
    stream = Stream(
        url=WEBSOCKET_URL,
        name="conversation-stream"
    )
    
    # Pass context parameters if provided
    if context:
        for key, value in context.items():
            stream.parameter(name=key, value=str(value))
    
    connect.append(stream)
    response.append(connect)
    
    # Fallback message if stream fails
    response.say(
        "I'm sorry, I'm having trouble connecting right now. Please try again later.",
        voice="Polly.Joanna",
        language="en-US"
    )
    
    return str(response)


def make_interactive_call(to_number, initial_message=None, context=None, status_callback=None):
    """
    Initiate an interactive phone call with WebSocket streaming.
    
    Args:
        to_number: Destination phone number (E.164 format)
        initial_message: Optional greeting before conversation starts
        context: Dictionary of context to pass to conversation server
        status_callback: Optional URL for call status updates
    
    Returns:
        Call SID
    """
    try:
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Generate TwiML
        twiml = generate_interactive_twiml(initial_message, context)
        
        # Prepare call parameters
        call_params = {
            "to": to_number,
            "from_": TWILIO_FROM_NUMBER,
            "twiml": twiml
        }
        
        # Add status callback if provided
        if status_callback:
            call_params["status_callback"] = status_callback
            call_params["status_callback_event"] = ["initiated", "ringing", "answered", "completed"]
        
        # Make the call
        call = client.calls.create(**call_params)
        
        print(f"✓ Interactive call initiated successfully!")
        print(f"  Call SID: {call.sid}")
        print(f"  To: {to_number}")
        print(f"  From: {TWILIO_FROM_NUMBER}")
        print(f"  Status: {call.status}")
        print(f"  WebSocket: {WEBSOCKET_URL}")
        if initial_message:
            print(f"  Initial message: {initial_message}")
        if context:
            print(f"  Context: {context}")
        
        return call.sid
        
    except Exception as e:
        print(f"✗ Error making call: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    global WEBSOCKET_URL
    parser = argparse.ArgumentParser(
        description="Make an interactive phone call using Twilio with WebSocket streaming"
    )
    parser.add_argument(
        "--to",
        required=True,
        help="Destination phone number (E.164 format, e.g., +15551234567)"
    )
    parser.add_argument(
        "--message",
        help="Optional initial greeting message before conversation starts"
    )
    parser.add_argument(
        "--context",
        help="Context string to pass to conversation (e.g., 'appointment_reminder')"
    )
    parser.add_argument(
        "--websocket-url",
        help=f"WebSocket server URL (default: {WEBSOCKET_URL})"
    )
    parser.add_argument(
        "--status-callback",
        help="Optional URL for call status updates"
    )
    
    args = parser.parse_args()
    
    # Validate phone number format
    if not args.to.startswith('+'):
        print("✗ Error: Phone number must be in E.164 format (start with +)", file=sys.stderr)
        sys.exit(1)
    
    # Override WebSocket URL if provided
    if args.websocket_url:
        WEBSOCKET_URL = args.websocket_url
    
    # Parse context
    context = None
    if args.context:
        context = {"context": args.context}
    
    # Make the call
    make_interactive_call(
        args.to,
        initial_message=args.message,
        context=context,
        status_callback=args.status_callback
    )


if __name__ == "__main__":
    main()
