#!/usr/bin/env python3
"""
Interactive Conversation WebSocket Server
Handles real-time audio streaming from Twilio for interactive voice conversations.
"""

import asyncio
import base64
import json
import os
import sys
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import websockets
# from websockets.server import serve  # Deprecated
import openai
import anthropic
from elevenlabs.client import ElevenLabs
import boto3

from audio_utils import AudioProcessor, AudioBuffer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "websocket": {
        "host": "0.0.0.0",
        "port": 18793,
    },
    "stt": {
        "provider": "openai",  # "openai" or "deepgram"
        "model": "whisper-1",
        "language": "en"
    },
    "llm": {
        "provider": "anthropic",  # "anthropic" or "openai"
        "model": "claude-3-5-sonnet-latest",
        "system_prompt": (
            "You are a friendly and helpful voice assistant. "
            "Keep your responses concise and natural for voice conversation. "
            "Speak in a conversational tone. Avoid long paragraphs. "
            "If you don't understand something, politely ask for clarification."
        ),
        "max_tokens": 150
    },
    "tts": {
        "provider": "elevenlabs",  # "elevenlabs" or "polly"
        "elevenlabs_voice": "21m00Tcm4TlvDq8ikWAM",
        "polly_voice": "Joanna",
        "elevenlabs_model": "eleven_monolingual_v1"
    },
    "conversation": {
        "silence_threshold_ms": 1500,  # Pause before processing speech
        "max_turn_duration_ms": 30000,  # Max speech duration
        "greeting": "Hello! How can I help you today?"
    }
}

# Initialize API clients
openai_client = None
anthropic_client = None
polly_client = None
elevenlabs_client = None

def initialize_clients():
    """Initialize API clients with credentials from environment."""
    global openai_client, anthropic_client, polly_client, elevenlabs_client
    
    # OpenAI (for Whisper STT and optionally GPT)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        openai_client = openai.OpenAI(api_key=openai_api_key)
        logger.info("✓ OpenAI client initialized")
    
    # Anthropic (for Claude)
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        logger.info("✓ Anthropic client initialized")
    
    # ElevenLabs
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    if elevenlabs_api_key:
        elevenlabs_client = ElevenLabs(api_key=elevenlabs_api_key)
        logger.info("✓ ElevenLabs client initialized")
    
    # AWS Polly (fallback TTS)
    try:
        polly_client = boto3.client('polly', region_name='us-east-1')
        logger.info("✓ AWS Polly client initialized")
    except Exception as e:
        logger.warning(f"Could not initialize Polly: {e}")


class ConversationSession:
    """Manages a single conversation session with a caller."""
    
    def __init__(self, websocket, stream_sid: str):
        self.websocket = websocket
        self.stream_sid = stream_sid
        self.call_sid: Optional[str] = None
        self.audio_buffer = AudioBuffer(max_duration_ms=CONFIG["conversation"]["max_turn_duration_ms"])
        self.conversation_history = []
        self.is_processing = False
        self.last_audio_time = None
        self.context = {}
        logger.info(f"Session created: {stream_sid}")
    
    async def handle_message(self, message: Dict[str, Any]):
        """Handle incoming WebSocket message from Twilio."""
        event = message.get("event")
        
        if event == "connected":
            logger.info(f"Connected: {self.stream_sid}")
        
        elif event == "start":
            self.call_sid = message.get("start", {}).get("callSid")
            # Extract custom parameters passed from TwiML
            custom_params = message.get("start", {}).get("customParameters", {})
            self.context = custom_params
            logger.info(f"Stream started: {self.stream_sid}, Call: {self.call_sid}")
            logger.info(f"Context: {self.context}")
            
            # Send initial greeting
            await self.speak(CONFIG["conversation"]["greeting"])
        
        elif event == "media":
            # Incoming audio from caller
            payload = message.get("media", {}).get("payload")
            if payload:
                await self.process_audio(payload)
        
        elif event == "stop":
            logger.info(f"Stream stopped: {self.stream_sid}")
    
    async def process_audio(self, payload: str):
        """Process incoming audio chunk from caller."""
        try:
            # Decode audio
            audio_chunk = AudioProcessor.decode_twilio_audio(payload)
            self.audio_buffer.add(audio_chunk)
            self.last_audio_time = datetime.now()
            
            # Check if we should process accumulated audio
            # (after silence threshold or max duration)
            if not self.is_processing:
                buffer_duration = self.audio_buffer.duration_ms()
                
                # Start processing if buffer has substantial audio
                if buffer_duration > 1000:  # At least 1 second
                    # Schedule silence detection
                    asyncio.create_task(self.check_for_speech_end())
        
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
    
    async def check_for_speech_end(self):
        """Check if caller has stopped speaking (silence detection)."""
        await asyncio.sleep(CONFIG["conversation"]["silence_threshold_ms"] / 1000)
        
        # Check if more audio arrived recently
        if self.last_audio_time:
            time_since_audio = (datetime.now() - self.last_audio_time).total_seconds() * 1000
            
            if time_since_audio >= CONFIG["conversation"]["silence_threshold_ms"]:
                # Sufficient silence detected, process the buffered audio
                await self.process_speech()
    
    async def process_speech(self):
        """Process buffered audio: STT -> LLM -> TTS."""
        if self.is_processing or self.audio_buffer.is_empty():
            return
        
        self.is_processing = True
        
        try:
            # Get audio buffer
            audio_data = self.audio_buffer.get_and_clear()
            
            if len(audio_data) < 8000:  # Less than 1 second
                logger.debug("Audio too short, ignoring")
                self.is_processing = False
                return
            
            logger.info(f"Processing speech ({len(audio_data)} bytes, {len(audio_data)/8000:.1f}s)")
            
            # Step 1: Speech-to-Text
            transcript = await self.transcribe_audio(audio_data)
            
            if not transcript or len(transcript.strip()) < 2:
                logger.info("No meaningful speech detected")
                self.is_processing = False
                return
            
            logger.info(f"Transcript: {transcript}")
            self.conversation_history.append({"role": "user", "content": transcript})
            
            # Step 2: Generate LLM response
            response_text = await self.generate_response(transcript)
            logger.info(f"Response: {response_text}")
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            # Step 3: Text-to-Speech and send to caller
            await self.speak(response_text)
        
        except Exception as e:
            logger.error(f"Error in speech processing: {e}", exc_info=True)
            await self.speak("I'm sorry, I didn't quite catch that. Could you repeat?")
        
        finally:
            self.is_processing = False
    
    async def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Convert audio to text using STT service."""
        try:
            if CONFIG["stt"]["provider"] == "openai" and openai_client:
                # Convert μ-law to WAV
                wav_data = AudioProcessor.mulaw_to_wav_bytes(audio_data)
                
                # Use Whisper API
                from io import BytesIO
                audio_file = BytesIO(wav_data)
                audio_file.name = "audio.wav"
                
                transcript = await asyncio.to_thread(
                    lambda: openai_client.audio.transcriptions.create(
                        model=CONFIG["stt"]["model"],
                        file=audio_file,
                        language=CONFIG["stt"]["language"]
                    )
                )
                
                return transcript.text.strip()
            
            else:
                logger.error("No STT provider configured")
                return None
        
        except Exception as e:
            logger.error(f"STT error: {e}", exc_info=True)
            return None
    
    async def generate_response(self, user_message: str) -> str:
        """Generate LLM response to user message."""
        try:
            if CONFIG["llm"]["provider"] == "anthropic" and anthropic_client:
                # Use Claude
                response = await asyncio.to_thread(
                    lambda: anthropic_client.messages.create(
                        model=CONFIG["llm"]["model"],
                        max_tokens=CONFIG["llm"]["max_tokens"],
                        system=CONFIG["llm"]["system_prompt"],
                        messages=self.conversation_history[-10:]  # Last 10 turns for context
                    )
                )
                return response.content[0].text.strip()
            
            elif CONFIG["llm"]["provider"] == "openai" and openai_client:
                # Use OpenAI GPT
                messages = [
                    {"role": "system", "content": CONFIG["llm"]["system_prompt"]}
                ] + self.conversation_history[-10:]
                
                response = await asyncio.to_thread(
                    lambda: openai_client.chat.completions.create(
                        model=CONFIG["llm"]["model"],
                        max_tokens=CONFIG["llm"]["max_tokens"],
                        messages=messages
                    )
                )
                return response.choices[0].message.content.strip()
            
            else:
                logger.error("No LLM provider configured")
                return "I'm having trouble connecting right now."
        
        except Exception as e:
            logger.error(f"LLM error: {e}", exc_info=True)
            return "I'm sorry, I'm having trouble understanding. Can you try again?"
    
    async def speak(self, text: str):
        """Convert text to speech and send to caller."""
        try:
            logger.info(f"Speaking: {text}")
            
            # Generate audio
            audio_data = await self.generate_speech(text)
            
            if not audio_data:
                logger.error("No audio generated")
                return
            
            # Convert to μ-law and send to Twilio
            await self.send_audio(audio_data)
        
        except Exception as e:
            logger.error(f"TTS error: {e}", exc_info=True)
    
    async def generate_speech(self, text: str) -> Optional[bytes]:
        """Generate speech audio from text."""
        try:
            if CONFIG["tts"]["provider"] == "elevenlabs" and elevenlabs_client:
                # Use ElevenLabs (generates PCM audio at various sample rates)
                audio_iter = await asyncio.to_thread(
                    lambda: elevenlabs_client.text_to_speech.convert(
                        text=text,
                        voice_id=CONFIG["tts"]["elevenlabs_voice"],
                        model_id=CONFIG["tts"]["elevenlabs_model"],
                        output_format="pcm_8000"
                    )
                )
                audio = b"".join(audio_iter)
                return audio
            
            else:
                # Use Polly as default
                return await self.generate_speech_polly(text)
        
        except Exception as e:
            logger.error(f"Speech generation error: {e}", exc_info=True)
            return await self.generate_speech_polly(text)  # Fallback
    
    async def generate_speech_polly(self, text: str) -> Optional[bytes]:
        """Generate speech using Amazon Polly."""
        try:
            if not polly_client:
                logger.error("Polly client not initialized")
                return None
            
            # Request PCM audio from Polly
            response = await asyncio.to_thread(
                lambda: polly_client.synthesize_speech(
                    Text=text,
                    OutputFormat='pcm',  # 16-bit PCM
                    VoiceId=CONFIG["tts"]["polly_voice"],
                    SampleRate='8000'  # Match Twilio's sample rate
                )
            )
            
            # Read audio stream
            if 'AudioStream' in response:
                return response['AudioStream'].read()
            
            return None
        
        except Exception as e:
            logger.error(f"Polly error: {e}", exc_info=True)
            return None
    
    async def send_audio(self, pcm_audio: bytes):
        """Send audio to caller via Twilio Media Stream."""
        try:
            # Convert PCM to μ-law
            mulaw_audio = AudioProcessor.linear_to_mulaw(pcm_audio)
            
            # Split into 20ms chunks (160 bytes at 8kHz)
            chunks = AudioProcessor.chunk_audio(mulaw_audio, chunk_size_ms=20)
            
            # Send each chunk
            for chunk in chunks:
                payload = AudioProcessor.encode_twilio_audio(chunk)
                
                message = {
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {
                        "payload": payload
                    }
                }
                
                await self.websocket.send(json.dumps(message))
                
                # Small delay to avoid overwhelming the stream
                await asyncio.sleep(0.02)  # 20ms
        
        except Exception as e:
            logger.error(f"Error sending audio: {e}", exc_info=True)


async def handle_connection(websocket):
    """Handle incoming WebSocket connection from Twilio."""
    logger.info(f"New connection from {websocket.remote_address}")
    
    session: Optional[ConversationSession] = None
    
    try:
        async for message_str in websocket:
            try:
                message = json.loads(message_str)
                
                # Create session on first message
                if session is None:
                    stream_sid = message.get("streamSid")
                    if stream_sid:
                        session = ConversationSession(websocket, stream_sid)
                
                # Handle message
                if session:
                    await session.handle_message(message)
            
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
            except Exception as e:
                logger.error(f"Error handling message: {e}", exc_info=True)
    
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed")
    except Exception as e:
        logger.error(f"Connection error: {e}", exc_info=True)
    finally:
        if session:
            logger.info(f"Session ended: {session.stream_sid}")


async def main():
    """Start the WebSocket server."""
    # Initialize API clients
    initialize_clients()
    
    # Verify we have necessary clients
    if not openai_client:
        logger.warning("OpenAI client not initialized - set OPENAI_API_KEY")
    if not anthropic_client and CONFIG["llm"]["provider"] == "anthropic":
        logger.warning("Anthropic client not initialized - set ANTHROPIC_API_KEY")
    if not polly_client:
        logger.warning("Polly client not initialized - configure AWS credentials")
    
    host = CONFIG["websocket"]["host"]
    port = CONFIG["websocket"]["port"]
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    logger.info(f"WebSocket URL: ws://{host}:{port}/media-stream")
    logger.info("Press Ctrl+C to stop")
    
    async with websockets.serve(handle_connection, host, port):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
