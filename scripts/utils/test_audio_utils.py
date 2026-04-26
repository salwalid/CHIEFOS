#!/usr/bin/env python3
"""
Test script for audio utilities
Verifies audio encoding/decoding functions work correctly.
"""

import sys
from audio_utils import AudioProcessor, AudioBuffer

def test_mulaw_conversion():
    """Test μ-law ↔ linear PCM conversion."""
    print("Testing μ-law conversion...")
    
    # Create test audio (silence)
    linear_audio = b'\x00\x00' * 1000  # 1000 samples of silence
    
    # Convert to μ-law
    mulaw_audio = AudioProcessor.linear_to_mulaw(linear_audio)
    print(f"  Linear size: {len(linear_audio)} bytes")
    print(f"  μ-law size: {len(mulaw_audio)} bytes")
    
    # Convert back
    linear_audio_2 = AudioProcessor.mulaw_to_linear(mulaw_audio)
    print(f"  Converted back: {len(linear_audio_2)} bytes")
    
    # Should be same size (though values may differ slightly due to compression)
    assert len(linear_audio) == len(linear_audio_2), "Size mismatch!"
    print("  ✓ Conversion successful")

def test_base64_encoding():
    """Test base64 encoding/decoding."""
    print("\nTesting base64 encoding...")
    
    test_data = b'\x80' * 160  # 160 bytes of μ-law audio
    
    # Encode
    encoded = AudioProcessor.encode_twilio_audio(test_data)
    print(f"  Original size: {len(test_data)} bytes")
    print(f"  Encoded size: {len(encoded)} chars")
    print(f"  Sample: {encoded[:40]}...")
    
    # Decode
    decoded = AudioProcessor.decode_twilio_audio(encoded)
    print(f"  Decoded size: {len(decoded)} bytes")
    
    assert test_data == decoded, "Encode/decode mismatch!"
    print("  ✓ Encoding successful")

def test_wav_conversion():
    """Test conversion to WAV format."""
    print("\nTesting WAV conversion...")
    
    # Create test μ-law audio
    mulaw_audio = b'\x80' * 8000  # 1 second at 8kHz
    
    # Convert to WAV
    wav_data = AudioProcessor.mulaw_to_wav_bytes(mulaw_audio)
    print(f"  μ-law size: {len(mulaw_audio)} bytes")
    print(f"  WAV size: {len(wav_data)} bytes")
    
    # WAV should have header + data
    assert len(wav_data) > len(mulaw_audio), "WAV should be larger (includes header)"
    assert wav_data[:4] == b'RIFF', "Should start with RIFF header"
    print("  ✓ WAV conversion successful")

def test_audio_chunking():
    """Test audio chunking."""
    print("\nTesting audio chunking...")
    
    # Create 1 second of audio (8000 bytes)
    audio_data = b'\x80' * 8000
    
    # Chunk into 20ms pieces
    chunks = AudioProcessor.chunk_audio(audio_data, chunk_size_ms=20)
    print(f"  Total audio: {len(audio_data)} bytes (1 second)")
    print(f"  Chunks: {len(chunks)}")
    print(f"  Chunk size: {len(chunks[0])} bytes")
    
    # Should be 50 chunks (1000ms / 20ms = 50)
    assert len(chunks) == 50, f"Expected 50 chunks, got {len(chunks)}"
    assert len(chunks[0]) == 160, f"Expected 160 bytes per chunk, got {len(chunks[0])}"
    print("  ✓ Chunking successful")

def test_audio_buffer():
    """Test audio buffer accumulation."""
    print("\nTesting audio buffer...")
    
    buffer = AudioBuffer(max_duration_ms=5000)
    
    # Add audio in chunks
    chunk = b'\x80' * 160  # 20ms chunk
    for i in range(100):  # Add 2 seconds of audio
        buffer.add(chunk)
    
    print(f"  Buffer size: {len(buffer.buffer)} bytes")
    print(f"  Buffer duration: {buffer.duration_ms()} ms")
    
    assert buffer.duration_ms() == 2000, f"Expected 2000ms, got {buffer.duration_ms()}"
    
    # Get and clear
    data = buffer.get_and_clear()
    assert len(data) == 160 * 100, "Should get all buffered data"
    assert buffer.is_empty(), "Buffer should be empty after get_and_clear"
    
    print("  ✓ Buffer successful")

def test_silence_detection():
    """Test silence detection."""
    print("\nTesting silence detection...")
    
    # True silence (zeros)
    silence = b'\x00\x00' * 1000
    is_silent = AudioProcessor.detect_silence(silence)
    print(f"  Zero audio is silent: {is_silent}")
    assert is_silent, "Should detect silence"
    
    # Loud audio (random high values)
    import random
    loud = bytes([random.randint(100, 200) for _ in range(2000)])
    is_silent = AudioProcessor.detect_silence(loud)
    print(f"  Loud audio is silent: {is_silent}")
    assert not is_silent, "Should not detect silence in loud audio"
    
    print("  ✓ Silence detection successful")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Audio Utilities Test Suite")
    print("=" * 60)
    
    try:
        test_mulaw_conversion()
        test_base64_encoding()
        test_wav_conversion()
        test_audio_chunking()
        test_audio_buffer()
        test_silence_detection()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
