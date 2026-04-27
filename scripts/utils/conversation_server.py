#!/usr/bin/env python3
"""
Alpha Conversation Server
Handles real-time audio streaming from Twilio for outbound task calls and inbound conversations.

Two modes:
  - Outbound/task: Alpha calls a third party to accomplish a specific task.
                   System prompt is built from the task brief passed by make_call.py.
                   Detects task completion and hangs up automatically.
  - Inbound/conversation: A caller speaks with Alpha directly.
                          Uses Alpha's default persona and greeting.
"""

import asyncio
import base64
import json
import os
import re
import sqlite3
import subprocess
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import websockets
import openai
import anthropic
from elevenlabs.client import ElevenLabs
import boto3
from twilio.rest import Client as TwilioClient

from audio_utils import AudioProcessor, AudioBuffer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ─── Environment ────────────────────────────────────────────────────────────

def load_env():
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    os.environ.setdefault(key.strip(), value.strip())

load_env()

_scripts_dir = Path(__file__).parent


# ─── Config ─────────────────────────────────────────────────────────────────

CONFIG = {
    "websocket": {
        "host": "0.0.0.0",
        "port": int(os.getenv('VOICE_PORT', '18793')),
    },
    "stt": {
        "provider": "openai",
        "model": "whisper-1",
        "language": "en"
    },
    "llm": {
        "provider": "anthropic",
        "model": os.getenv('LLM_MODEL', 'claude-sonnet-4-6'),
        "max_tokens": 200
    },
    "tts": {
        "provider": "elevenlabs",
        "elevenlabs_voice": os.getenv('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM'),
        "elevenlabs_model": "eleven_turbo_v2",
        "polly_voice": os.getenv('POLLY_VOICE', 'Joanna'),
    },
    "conversation": {
        "silence_threshold_ms": 1200,
        "max_turn_duration_ms": 30000,
        "greeting": "Hello, how can I help you today?",
    },
    "paths": {
        "db": os.getenv('DB_PATH', str(_scripts_dir.parent.parent / 'chiefos.db')),
        "telegram_script": str(_scripts_dir / 'send-telegram-alert.sh'),
    }
}

# Regex to detect task completion markers from the LLM
COMPLETION_RE = re.compile(
    r'\[(TASK_COMPLETE|TASK_FAILED):\s*([^\]]+)\]',
    re.IGNORECASE
)


# ─── API clients ────────────────────────────────────────────────────────────

openai_client = None
anthropic_client = None
polly_client = None
elevenlabs_client = None
twilio_client = None


def initialize_clients():
    global openai_client, anthropic_client, polly_client, elevenlabs_client, twilio_client

    key = os.getenv("OPENAI_API_KEY")
    if key:
        openai_client = openai.OpenAI(api_key=key)
        logger.info("✓ OpenAI (Whisper STT)")

    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        anthropic_client = anthropic.Anthropic(api_key=key)
        logger.info("✓ Anthropic (Claude LLM)")

    key = os.getenv("ELEVENLABS_API_KEY")
    if key:
        elevenlabs_client = ElevenLabs(api_key=key)
        logger.info("✓ ElevenLabs (TTS)")

    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    if sid and token:
        twilio_client = TwilioClient(sid, token)
        logger.info("✓ Twilio (call control)")

    try:
        polly_client = boto3.client('polly', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
        logger.info("✓ AWS Polly (TTS fallback)")
    except Exception as e:
        logger.warning(f"Polly unavailable: {e}")


# ─── System prompt builder ───────────────────────────────────────────────────

def build_system_prompt(context: dict) -> str:
    """
    Build a dynamic system prompt from call context.
    Outbound task calls get a precise task brief.
    Inbound/conversation calls get a generic helpful assistant prompt.
    """
    task = context.get('task', '').strip()
    caller_name = context.get('caller_name', os.getenv('CALLER_NAME', 'the user'))
    callback = context.get('callback_number', os.getenv('CALLBACK_NUMBER', ''))

    if task:
        callback_line = f"- If asked for a callback number: {callback}\n" if callback else ""
        return (
            f"You are a voice assistant making a phone call on behalf of {caller_name}.\n\n"
            f"YOUR TASK: {task}\n\n"
            f"RULES:\n"
            f"- Be natural, warm, and concise. This is a real live phone call.\n"
            f"- Keep every response to 1-3 sentences maximum — this is voice, not text.\n"
            f"- Do NOT use filler phrases like 'Certainly!', 'Of course!', 'Absolutely!', or 'Great!'.\n"
            f"{callback_line}"
            f"- If asked whether you are AI or a bot: say you are a digital assistant "
            f"calling on behalf of {caller_name}.\n"
            f"- Listen carefully and respond only to what was actually said.\n"
            f"- When your task is fully complete and you are saying goodbye, "
            f"append this exact marker to your response:\n"
            f"  [TASK_COMPLETE: one-sentence summary of outcome]\n"
            f"- If the task cannot be completed for any reason, say a polite goodbye and append:\n"
            f"  [TASK_FAILED: reason]\n"
            f"- Example: 'Thank you so much, see you Saturday. "
            f"[TASK_COMPLETE: Table booked for 2 at 8pm Sat, confirmed by Maria]'\n"
            f"- The marker is never spoken aloud — it is your internal signal only."
        )

    return (
        "You are a helpful voice assistant. "
        "Be warm, concise, and natural. "
        "Keep every response to 1-2 sentences — this is a phone call."
    )


# ─── Session ─────────────────────────────────────────────────────────────────

class ConversationSession:
    """Manages a single call session."""

    def __init__(self, websocket, stream_sid: str):
        self.websocket = websocket
        self.stream_sid = stream_sid
        self.call_sid: Optional[str] = None
        self.audio_buffer = AudioBuffer(
            max_duration_ms=CONFIG["conversation"]["max_turn_duration_ms"]
        )
        self.conversation_history = []
        self.is_processing = False
        self.last_audio_time = None
        self.context: dict = {}
        self.system_prompt: str = ""
        self.task_mode: bool = False
        self.task_done: bool = False
        logger.info(f"Session created: {stream_sid}")

    async def handle_message(self, message: Dict[str, Any]):
        event = message.get("event")

        if event == "connected":
            logger.info("WebSocket connected")

        elif event == "start":
            self.call_sid = message.get("start", {}).get("callSid")
            self.context = message.get("start", {}).get("customParameters", {})
            self.system_prompt = build_system_prompt(self.context)
            self.task_mode = bool(self.context.get('task'))

            logger.info(f"Call started — SID: {self.call_sid} — task_mode: {self.task_mode}")
            if self.task_mode:
                logger.info(f"Task: {self.context.get('task')}")
            else:
                await self.speak(CONFIG["conversation"]["greeting"])

        elif event == "media":
            if self.task_done:
                return
            payload = message.get("media", {}).get("payload")
            if payload:
                await self.process_audio(payload)

        elif event == "stop":
            logger.info(f"Stream stopped: {self.stream_sid}")

    async def process_audio(self, payload: str):
        try:
            audio_chunk = AudioProcessor.decode_twilio_audio(payload)
            self.audio_buffer.add(audio_chunk)
            self.last_audio_time = datetime.now()

            if not self.is_processing:
                if self.audio_buffer.duration_ms() > 800:
                    asyncio.create_task(self.check_for_speech_end())

        except Exception as e:
            logger.error(f"Audio processing error: {e}", exc_info=True)

    async def check_for_speech_end(self):
        await asyncio.sleep(CONFIG["conversation"]["silence_threshold_ms"] / 1000)

        if self.last_audio_time:
            elapsed = (datetime.now() - self.last_audio_time).total_seconds() * 1000
            if elapsed >= CONFIG["conversation"]["silence_threshold_ms"]:
                await self.process_speech()

    async def process_speech(self):
        if self.is_processing or self.audio_buffer.is_empty() or self.task_done:
            return

        self.is_processing = True
        try:
            audio_data = self.audio_buffer.get_and_clear()

            if len(audio_data) < 6400:
                self.is_processing = False
                return

            logger.info(f"Processing {len(audio_data)/8000:.1f}s of audio")

            transcript = await self.transcribe(audio_data)
            if not transcript or len(transcript.strip()) < 2:
                self.is_processing = False
                return

            logger.info(f"Heard: {transcript}")
            self.conversation_history.append({"role": "user", "content": transcript})

            response_text = await self.generate_response()
            logger.info(f"Responding: {response_text}")

            match = COMPLETION_RE.search(response_text)
            if match:
                status = match.group(1).upper()
                outcome = match.group(2).strip()
                clean_text = COMPLETION_RE.sub('', response_text).strip()
                success = status == 'TASK_COMPLETE'
                self.task_done = True

                self.conversation_history.append({"role": "assistant", "content": clean_text})
                await self.speak(clean_text)
                await asyncio.sleep(3)
                await self.complete_task(outcome, success)
            else:
                self.conversation_history.append({"role": "assistant", "content": response_text})
                await self.speak(response_text)

        except Exception as e:
            logger.error(f"Speech processing error: {e}", exc_info=True)
            await self.speak("I'm sorry, could you repeat that?")
        finally:
            self.is_processing = False

    async def transcribe(self, audio_data: bytes) -> Optional[str]:
        try:
            if openai_client:
                from io import BytesIO
                wav_data = AudioProcessor.mulaw_to_wav_bytes(audio_data)
                audio_file = BytesIO(wav_data)
                audio_file.name = "audio.wav"
                result = await asyncio.to_thread(
                    lambda: openai_client.audio.transcriptions.create(
                        model=CONFIG["stt"]["model"],
                        file=audio_file,
                        language=CONFIG["stt"]["language"]
                    )
                )
                return result.text.strip()
        except Exception as e:
            logger.error(f"STT error: {e}", exc_info=True)
        return None

    async def generate_response(self) -> str:
        try:
            if anthropic_client:
                response = await asyncio.to_thread(
                    lambda: anthropic_client.messages.create(
                        model=CONFIG["llm"]["model"],
                        max_tokens=CONFIG["llm"]["max_tokens"],
                        system=self.system_prompt,
                        messages=self.conversation_history[-10:]
                    )
                )
                return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"LLM error: {e}", exc_info=True)
        return "I'm sorry, could you repeat that?"

    async def speak(self, text: str):
        if not text:
            return
        try:
            audio_data = await self.generate_speech(text)
            if audio_data:
                await self.send_audio(audio_data)
        except Exception as e:
            logger.error(f"TTS error: {e}", exc_info=True)

    async def generate_speech(self, text: str) -> Optional[bytes]:
        try:
            if elevenlabs_client:
                audio_iter = await asyncio.to_thread(
                    lambda: elevenlabs_client.text_to_speech.convert(
                        text=text,
                        voice_id=CONFIG["tts"]["elevenlabs_voice"],
                        model_id=CONFIG["tts"]["elevenlabs_model"],
                        output_format="pcm_8000"
                    )
                )
                return b"".join(audio_iter)
        except Exception as e:
            logger.warning(f"ElevenLabs error, falling back to Polly: {e}")

        return await self.generate_speech_polly(text)

    async def generate_speech_polly(self, text: str) -> Optional[bytes]:
        try:
            if polly_client:
                response = await asyncio.to_thread(
                    lambda: polly_client.synthesize_speech(
                        Text=text,
                        OutputFormat='pcm',
                        VoiceId=CONFIG["tts"]["polly_voice"],
                        SampleRate='8000'
                    )
                )
                if 'AudioStream' in response:
                    return response['AudioStream'].read()
        except Exception as e:
            logger.error(f"Polly error: {e}", exc_info=True)
        return None

    async def send_audio(self, pcm_audio: bytes):
        try:
            mulaw_audio = AudioProcessor.linear_to_mulaw(pcm_audio)
            chunks = AudioProcessor.chunk_audio(mulaw_audio, chunk_size_ms=20)
            for chunk in chunks:
                payload = AudioProcessor.encode_twilio_audio(chunk)
                await self.websocket.send(json.dumps({
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {"payload": payload}
                }))
                await asyncio.sleep(0.02)
        except Exception as e:
            logger.error(f"Audio send error: {e}", exc_info=True)

    # ─── Task completion ────────────────────────────────────────────────────

    async def complete_task(self, outcome: str, success: bool):
        logger.info(f"Task {'✓ complete' if success else '✗ failed'}: {outcome}")
        await asyncio.gather(
            self.log_to_db(outcome, success),
            self.notify_telegram(outcome, success),
        )
        await self.hangup()

    async def hangup(self):
        if self.call_sid and twilio_client:
            try:
                await asyncio.to_thread(
                    lambda: twilio_client.calls(self.call_sid).update(status='completed')
                )
                logger.info("Call ended")
            except Exception as e:
                logger.error(f"Hangup error: {e}")

    async def log_to_db(self, outcome: str, success: bool):
        task = self.context.get('task', 'Voice call')
        db_path = CONFIG["paths"]["db"]

        def insert():
            try:
                conn = sqlite3.connect(db_path)
                conn.execute(
                    "INSERT INTO chronicles "
                    "(timestamp, component, event, lesson_learned, session_date) "
                    "VALUES (datetime('now'), 'voice_call', ?, ?, date('now'))",
                    (
                        f"Outbound call: {task[:200]}",
                        f"{'SUCCESS' if success else 'FAILED'}: {outcome}"
                    )
                )
                conn.commit()
                conn.close()
                logger.info("Logged to chronicles")
            except Exception as e:
                logger.error(f"DB log error: {e}")

        await asyncio.to_thread(insert)

    async def notify_telegram(self, outcome: str, success: bool):
        task = self.context.get('task', 'Voice call')
        icon = "✅" if success else "❌"
        message = f"{icon} Call complete\nTask: {task}\nOutcome: {outcome}"
        telegram_script = CONFIG["paths"]["telegram_script"]

        try:
            await asyncio.to_thread(
                lambda: subprocess.run(
                    ['bash', telegram_script, message],
                    capture_output=True, timeout=10
                )
            )
            logger.info("Telegram notification sent")
        except Exception as e:
            logger.error(f"Telegram error: {e}")


# ─── WebSocket handler ───────────────────────────────────────────────────────

async def handle_connection(websocket):
    logger.info(f"New connection from {websocket.remote_address}")
    session: Optional[ConversationSession] = None

    try:
        async for message_str in websocket:
            try:
                message = json.loads(message_str)

                if session is None:
                    stream_sid = message.get("streamSid")
                    if stream_sid:
                        session = ConversationSession(websocket, stream_sid)

                if session:
                    await session.handle_message(message)

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
            except Exception as e:
                logger.error(f"Message error: {e}", exc_info=True)

    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed")
    except Exception as e:
        logger.error(f"Connection error: {e}", exc_info=True)
    finally:
        if session:
            logger.info(f"Session ended: {session.stream_sid}")


# ─── Main ────────────────────────────────────────────────────────────────────

async def main():
    initialize_clients()

    if not openai_client:
        logger.warning("No OPENAI_API_KEY — STT will not work")
    if not anthropic_client:
        logger.warning("No ANTHROPIC_API_KEY — LLM will not work")
    if not elevenlabs_client:
        logger.warning("No ELEVENLABS_API_KEY — falling back to Polly")

    host = CONFIG["websocket"]["host"]
    port = CONFIG["websocket"]["port"]

    logger.info(f"Conversation server starting on {host}:{port}")
    async with websockets.serve(handle_connection, host, port):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")
        sys.exit(0)
