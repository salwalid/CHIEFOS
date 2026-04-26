"""
Audio utilities for Twilio Media Streams
Handles encoding/decoding between μ-law, PCM, and other formats.
"""

import base64
import audioop
import io
import numpy as np
from typing import Optional


class AudioProcessor:
    """Handle audio conversion for Twilio Media Streams."""
    
    # Twilio uses 8kHz μ-law encoded audio
    SAMPLE_RATE = 8000
    SAMPLE_WIDTH = 1  # 8-bit μ-law
    CHANNELS = 1  # Mono
    
    @staticmethod
    def mulaw_to_linear(mulaw_data: bytes) -> bytes:
        """
        Convert μ-law encoded audio to linear PCM.
        
        Args:
            mulaw_data: μ-law encoded audio bytes
        
        Returns:
            Linear PCM audio bytes (16-bit)
        """
        return audioop.ulaw2lin(mulaw_data, 2)  # 2 = 16-bit output
    
    @staticmethod
    def linear_to_mulaw(linear_data: bytes) -> bytes:
        """
        Convert linear PCM audio to μ-law encoding.
        
        Args:
            linear_data: Linear PCM audio bytes (16-bit)
        
        Returns:
            μ-law encoded audio bytes
        """
        return audioop.lin2ulaw(linear_data, 2)  # 2 = 16-bit input
    
    @staticmethod
    def decode_twilio_audio(payload: str) -> bytes:
        """
        Decode base64-encoded μ-law audio from Twilio.
        
        Args:
            payload: Base64-encoded μ-law audio string
        
        Returns:
            Raw μ-law audio bytes
        """
        return base64.b64decode(payload)
    
    @staticmethod
    def encode_twilio_audio(audio_data: bytes) -> str:
        """
        Encode μ-law audio to base64 for Twilio.
        
        Args:
            audio_data: Raw μ-law audio bytes
        
        Returns:
            Base64-encoded string
        """
        return base64.b64encode(audio_data).decode('utf-8')
    
    @staticmethod
    def mulaw_to_wav_bytes(mulaw_data: bytes, sample_rate: int = 8000) -> bytes:
        """
        Convert μ-law audio to WAV format bytes (for STT APIs).
        
        Args:
            mulaw_data: μ-law encoded audio bytes
            sample_rate: Sample rate (default 8000 Hz)
        
        Returns:
            WAV file bytes
        """
        import wave
        
        # Convert to linear PCM
        linear_data = AudioProcessor.mulaw_to_linear(mulaw_data)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(linear_data)
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    @staticmethod
    def pcm_to_mulaw(pcm_data: bytes, source_rate: int = 24000, target_rate: int = 8000) -> bytes:
        """
        Convert PCM audio (from TTS) to μ-law for Twilio.
        Handles resampling if needed.
        
        Args:
            pcm_data: Linear PCM audio bytes (16-bit)
            source_rate: Source sample rate (e.g., 24000 for ElevenLabs)
            target_rate: Target sample rate (8000 for Twilio)
        
        Returns:
            μ-law encoded audio bytes at target rate
        """
        # Resample if needed
        if source_rate != target_rate:
            pcm_data = audioop.ratecv(
                pcm_data,
                2,  # 16-bit samples
                1,  # Mono
                source_rate,
                target_rate,
                None
            )[0]
        
        # Convert to μ-law
        return AudioProcessor.linear_to_mulaw(pcm_data)
    
    @staticmethod
    def detect_silence(audio_data: bytes, threshold: float = 0.02) -> bool:
        """
        Detect if audio chunk is mostly silence.
        
        Args:
            audio_data: Linear PCM audio bytes (16-bit)
            threshold: RMS threshold (0-1 scale)
        
        Returns:
            True if audio is mostly silent
        """
        if len(audio_data) < 2:
            return True
        
        # Calculate RMS (root mean square) of audio
        rms = audioop.rms(audio_data, 2)  # 2 = 16-bit samples
        
        # Normalize to 0-1 scale (16-bit max is 32768)
        normalized_rms = rms / 32768.0
        
        return normalized_rms < threshold
    
    @staticmethod
    def chunk_audio(audio_data: bytes, chunk_size_ms: int = 20) -> list:
        """
        Split audio into chunks of specified duration.
        
        Args:
            audio_data: Audio bytes (μ-law, 8kHz)
            chunk_size_ms: Chunk duration in milliseconds
        
        Returns:
            List of audio chunks
        """
        # Calculate bytes per chunk
        # 8000 samples/sec * (chunk_size_ms / 1000) * 1 byte/sample
        bytes_per_chunk = int(8000 * chunk_size_ms / 1000)
        
        chunks = []
        for i in range(0, len(audio_data), bytes_per_chunk):
            chunks.append(audio_data[i:i + bytes_per_chunk])
        
        return chunks


class AudioBuffer:
    """Buffer for accumulating audio chunks."""
    
    def __init__(self, max_duration_ms: int = 10000):
        """
        Initialize audio buffer.
        
        Args:
            max_duration_ms: Maximum buffer duration in milliseconds
        """
        self.buffer = bytearray()
        self.max_bytes = int(8000 * max_duration_ms / 1000)  # 8kHz, 1 byte/sample
        self.silence_threshold = 1500  # 1.5 seconds of silence
        self.last_audio_timestamp = 0
    
    def add(self, audio_chunk: bytes):
        """Add audio chunk to buffer."""
        self.buffer.extend(audio_chunk)
        
        # Trim if exceeds max size
        if len(self.buffer) > self.max_bytes:
            # Keep most recent audio
            self.buffer = self.buffer[-self.max_bytes:]
    
    def clear(self):
        """Clear the buffer."""
        self.buffer.clear()
    
    def get(self) -> bytes:
        """Get buffered audio without clearing."""
        return bytes(self.buffer)
    
    def get_and_clear(self) -> bytes:
        """Get buffered audio and clear the buffer."""
        data = bytes(self.buffer)
        self.clear()
        return data
    
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self.buffer) == 0
    
    def duration_ms(self) -> int:
        """Get current buffer duration in milliseconds."""
        # 8000 bytes/sec, so ms = (bytes / 8000) * 1000
        return int((len(self.buffer) / 8000) * 1000)
