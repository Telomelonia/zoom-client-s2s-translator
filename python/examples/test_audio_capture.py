"""
Example script demonstrating audio capture usage.

This script shows how to use MicrophoneCapture and AudioDeviceManager
to capture audio from the microphone in real-time.

Usage:
    python examples/test_audio_capture.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio import (
    MicrophoneCapture,
    SystemAudioCapture,
    AudioDeviceManager,
    list_audio_devices,
    find_loopback_device,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def test_microphone_capture(duration_seconds: int = 5):
    """
    Test microphone capture for a specified duration.

    Args:
        duration_seconds: How long to capture audio
    """
    logger.info("=== Testing Microphone Capture ===")

    # List available devices
    with AudioDeviceManager() as manager:
        manager.print_all_devices()

        default_input = manager.get_default_input_device()
        if not default_input:
            logger.error("No default input device found!")
            return

        logger.info(f"\nUsing device: {default_input}")

    # Capture audio
    async with MicrophoneCapture() as mic:
        logger.info(f"Capturing audio for {duration_seconds} seconds...")
        logger.info("Speak into your microphone!")

        loop = asyncio.get_running_loop()
        start_time = loop.time()
        chunks_received = 0
        total_bytes = 0

        while (loop.time() - start_time) < duration_seconds:
            try:
                chunk = await mic.read_chunk(timeout=0.5)
                chunks_received += 1
                total_bytes += len(chunk.data)

                # Log every 10 chunks
                if chunks_received % 10 == 0:
                    logger.info(
                        f"Received {chunks_received} chunks, "
                        f"{total_bytes} bytes, "
                        f"{chunk.duration_ms:.1f}ms per chunk"
                    )

            except asyncio.TimeoutError:
                logger.debug("No audio data (timeout)")

        # Show final stats
        logger.info(f"\nFinal stats: {mic.stats}")
        logger.info(
            f"Captured {chunks_received} chunks, "
            f"{total_bytes / 1024:.1f} KB in {duration_seconds}s"
        )


async def test_system_audio_capture(duration_seconds: int = 5):
    """
    Test system audio capture (requires virtual audio device).

    Args:
        duration_seconds: How long to capture audio
    """
    logger.info("\n=== Testing System Audio Capture ===")

    # Find loopback device
    loopback = find_loopback_device()
    if not loopback:
        logger.error(
            "No virtual audio device found! "
            "Install BlackHole (macOS) or VB-Audio Cable (Windows)"
        )
        return

    logger.info(f"Using loopback device: {loopback}")

    # Capture system audio
    async with SystemAudioCapture(device_index=loopback.index) as system:
        logger.info(f"Capturing system audio for {duration_seconds} seconds...")
        logger.info("Play some audio on your computer!")

        loop = asyncio.get_running_loop()
        start_time = loop.time()
        chunks_received = 0
        total_bytes = 0

        while (loop.time() - start_time) < duration_seconds:
            try:
                chunk = await system.read_chunk(timeout=0.5)
                chunks_received += 1
                total_bytes += len(chunk.data)

                # Log every 10 chunks
                if chunks_received % 10 == 0:
                    logger.info(
                        f"Received {chunks_received} chunks, "
                        f"{total_bytes} bytes"
                    )

            except asyncio.TimeoutError:
                logger.debug("No audio data (timeout)")

        # Show final stats
        logger.info(f"\nFinal stats: {system.stats}")
        logger.info(
            f"Captured {chunks_received} chunks, "
            f"{total_bytes / 1024:.1f} KB in {duration_seconds}s"
        )


async def test_device_enumeration():
    """Test audio device enumeration and filtering."""
    logger.info("\n=== Testing Device Enumeration ===")

    devices = list_audio_devices()
    logger.info(f"Found {len(devices)} total devices")

    with AudioDeviceManager() as manager:
        input_devices = manager.get_input_devices(include_virtual=False)
        logger.info(f"Physical input devices: {len(input_devices)}")
        for device in input_devices:
            logger.info(f"  {device}")

        virtual_devices = manager.get_loopback_devices()
        logger.info(f"\nVirtual/Loopback devices: {len(virtual_devices)}")
        for device in virtual_devices:
            logger.info(f"  {device}")


async def main():
    """Run all audio capture tests."""
    logger.info("Starting audio capture tests\n")

    try:
        # Test device enumeration
        await test_device_enumeration()

        # Test microphone capture
        await test_microphone_capture(duration_seconds=5)

        # Test system audio capture (if virtual device available)
        # await test_system_audio_capture(duration_seconds=5)

        logger.info("\n=== All tests complete ===")

    except KeyboardInterrupt:
        logger.info("\nTests interrupted by user")
    except Exception as e:
        logger.exception(f"Error during tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
