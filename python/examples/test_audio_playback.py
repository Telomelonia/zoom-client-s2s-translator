"""
Example script demonstrating audio playback usage.

This script shows how to use SpeakerOutput and VirtualMicOutput
to play audio in real-time.

Usage:
    python examples/test_audio_playback.py
"""

import asyncio
import logging
import math
import struct
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio import (
    SpeakerOutput,
    VirtualMicOutput,
    AudioDeviceManager,
    find_speaker_device,
    find_virtual_mic_device,
    SAMPLE_RATE_OUTPUT,
    CHUNK_SIZE,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def generate_sine_wave(
    frequency: float,
    duration_seconds: float,
    sample_rate: int = SAMPLE_RATE_OUTPUT,
    amplitude: float = 0.5,
) -> bytes:
    """
    Generate a sine wave tone as PCM audio data.

    Args:
        frequency: Tone frequency in Hz
        duration_seconds: Duration of the tone
        sample_rate: Audio sample rate
        amplitude: Volume (0.0 to 1.0)

    Returns:
        Raw PCM audio bytes (16-bit signed, mono)
    """
    num_samples = int(sample_rate * duration_seconds)
    max_amplitude = int(32767 * amplitude)

    audio_data = b""
    for i in range(num_samples):
        t = i / sample_rate
        value = int(max_amplitude * math.sin(2 * math.pi * frequency * t))
        audio_data += struct.pack("<h", value)

    return audio_data


async def test_speaker_output(duration_seconds: float = 3.0):
    """
    Test speaker output by playing a test tone.

    Args:
        duration_seconds: How long to play the tone
    """
    logger.info("=== Testing Speaker Output ===")

    # Show available output devices
    with AudioDeviceManager() as manager:
        output_devices = manager.get_output_devices()
        logger.info(f"Found {len(output_devices)} output devices:")
        for device in output_devices:
            logger.info(f"  {device}")

        default_output = manager.get_default_output_device()
        if default_output:
            logger.info(f"\nDefault output: {default_output.name}")

    # Generate test tones
    logger.info("\nGenerating test tones...")
    tone_440hz = generate_sine_wave(440, 1.0)  # A4 note
    tone_880hz = generate_sine_wave(880, 1.0)  # A5 note
    tone_523hz = generate_sine_wave(523.25, 1.0)  # C5 note

    # Play through speakers
    logger.info("Playing test tones through speakers...")
    logger.info("You should hear: A4 (440Hz) -> C5 (523Hz) -> A5 (880Hz)")

    async with SpeakerOutput() as speaker:
        # Play tones by writing chunks
        chunk_bytes = CHUNK_SIZE * 2  # 16-bit = 2 bytes per sample

        # Play 440Hz
        logger.info("Playing 440Hz (A4)...")
        for i in range(0, len(tone_440hz), chunk_bytes):
            chunk = tone_440hz[i:i + chunk_bytes]
            if len(chunk) == chunk_bytes:
                await speaker.write_chunk(chunk)

        # Small pause
        await asyncio.sleep(0.2)

        # Play 523Hz
        logger.info("Playing 523Hz (C5)...")
        for i in range(0, len(tone_523hz), chunk_bytes):
            chunk = tone_523hz[i:i + chunk_bytes]
            if len(chunk) == chunk_bytes:
                await speaker.write_chunk(chunk)

        # Small pause
        await asyncio.sleep(0.2)

        # Play 880Hz
        logger.info("Playing 880Hz (A5)...")
        for i in range(0, len(tone_880hz), chunk_bytes):
            chunk = tone_880hz[i:i + chunk_bytes]
            if len(chunk) == chunk_bytes:
                await speaker.write_chunk(chunk)

        # Wait for playback to finish
        await asyncio.sleep(0.5)

        logger.info(f"\nPlayback stats: {speaker.stats}")


async def test_virtual_mic_output():
    """
    Test virtual microphone output (if available).
    """
    logger.info("\n=== Testing Virtual Mic Output ===")

    virtual_mic = find_virtual_mic_device()
    if not virtual_mic:
        logger.warning(
            "No virtual audio device found!\n"
            "Install BlackHole (macOS): brew install blackhole-2ch\n"
            "Or VB-Audio Cable (Windows): https://vb-audio.com/Cable/"
        )
        return

    logger.info(f"Found virtual mic device: {virtual_mic}")
    logger.info("Sending test tone to virtual microphone...")
    logger.info("(You can monitor this in another app that uses the virtual mic as input)")

    # Generate test tone
    tone = generate_sine_wave(660, 2.0)  # E5 note for 2 seconds
    chunk_bytes = CHUNK_SIZE * 2

    async with VirtualMicOutput(device_index=virtual_mic.index) as output:
        for i in range(0, len(tone), chunk_bytes):
            chunk = tone[i:i + chunk_bytes]
            if len(chunk) == chunk_bytes:
                await output.write_chunk(chunk)

        await asyncio.sleep(0.5)
        logger.info(f"Virtual mic stats: {output.stats}")


async def test_loopback():
    """
    Test microphone to speaker loopback (if capture module available).
    """
    logger.info("\n=== Testing Audio Loopback ===")

    try:
        from audio import MicrophoneCapture

        logger.info("Recording from microphone and playing through speakers...")
        logger.info("Speak into your microphone! (5 second test)")
        logger.info("WARNING: Use headphones to avoid feedback!")

        async with MicrophoneCapture() as mic, SpeakerOutput() as speaker:
            loop = asyncio.get_running_loop()
            start_time = loop.time()

            while (loop.time() - start_time) < 5:
                try:
                    chunk = await mic.read_chunk(timeout=0.1)
                    # Note: Sample rate mismatch (16kHz -> 24kHz) will cause pitch shift
                    # This is expected - the real Gemini pipeline outputs 24kHz
                    speaker.write_chunk_nowait(chunk.data)
                except asyncio.TimeoutError:
                    pass

        logger.info("Loopback test complete!")

    except ImportError:
        logger.warning("MicrophoneCapture not available, skipping loopback test")


async def test_device_enumeration():
    """Test output device enumeration."""
    logger.info("\n=== Testing Output Device Enumeration ===")

    speaker = find_speaker_device()
    if speaker:
        logger.info(f"Default speaker: {speaker}")
    else:
        logger.warning("No default speaker found")

    virtual_mic = find_virtual_mic_device()
    if virtual_mic:
        logger.info(f"Virtual mic device: {virtual_mic}")
    else:
        logger.info("No virtual mic device found (install BlackHole or VB-Audio)")


async def main():
    """Run all audio playback tests."""
    logger.info("Starting audio playback tests\n")

    try:
        # Test device enumeration
        await test_device_enumeration()

        # Test speaker output
        await test_speaker_output()

        # Test virtual mic (if available)
        await test_virtual_mic_output()

        # Uncomment to test loopback (use headphones!)
        # await test_loopback()

        logger.info("\n=== All tests complete ===")

    except KeyboardInterrupt:
        logger.info("\nTests interrupted by user")
    except Exception as e:
        logger.exception(f"Error during tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
