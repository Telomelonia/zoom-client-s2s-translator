#!/usr/bin/env python3
"""
Test script for Gemini Speech-to-Speech Translation.

This script demonstrates the integration of Gemini Live API with audio
capture and playback for real-time translation.

Usage:
    # Test basic API connection
    python test_gemini_translation.py --test-connection

    # Test outgoing translation (mic -> speakers for development)
    python test_gemini_translation.py --test-outgoing --target ja-JP

    # Test full pipeline (mic -> Gemini -> virtual mic)
    python test_gemini_translation.py --test-pipeline --target es-ES

Requirements:
    - GOOGLE_CLOUD_PROJECT environment variable set
    - Google Cloud authentication (run: gcloud auth application-default login)
    - Microphone access
    - Speaker output
    - (Optional) Virtual audio device (BlackHole on macOS)
"""

import asyncio
import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio import (
    list_audio_devices,
    find_microphone_device,
    find_speaker_device,
    find_virtual_mic_device,
    MicrophoneCapture,
    SpeakerOutput,
)
from gemini import (
    GeminiConfig,
    SupportedLanguage,
    GeminiS2STClient,
    get_language_choices,
)
from routing import TranslationPipeline, PipelineMode

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_gcp_credentials() -> bool:
    """
    Check if Google Cloud credentials are configured.

    Returns:
        True if GCP credentials are available, False otherwise
    """
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        logger.error(
            "GOOGLE_CLOUD_PROJECT environment variable not set. "
            "Please set it before running tests."
        )
        logger.error("Example: export GOOGLE_CLOUD_PROJECT='your-gcp-project-id'")
        logger.error("")
        logger.error("Also ensure you've authenticated with:")
        logger.error("  gcloud auth application-default login")
        return False

    logger.info(f"Using GCP project: {project}")
    return True


def list_available_languages() -> None:
    """Print all available languages for translation."""
    print("\n=== Available Languages ===")
    choices = get_language_choices()
    for display_name, lang_enum in sorted(choices.items()):
        print(f"  {display_name:30s} -> {lang_enum.language_code}")
    print()


def list_devices() -> None:
    """List all available audio devices."""
    print("\n=== Audio Devices ===")
    devices = list_audio_devices()

    print("\nInput Devices:")
    for device in devices:
        if device.max_input_channels > 0:
            indicator = " [DEFAULT]" if device.is_default_input else ""
            print(
                f"  [{device.index}] {device.name} "
                f"({device.max_input_channels} channels){indicator}"
            )

    print("\nOutput Devices:")
    for device in devices:
        if device.max_output_channels > 0:
            indicator = " [DEFAULT]" if device.is_default_output else ""
            print(
                f"  [{device.index}] {device.name} "
                f"({device.max_output_channels} channels){indicator}"
            )

    # Show recommended devices
    print("\n=== Recommended Devices ===")
    mic = find_microphone_device()
    if mic:
        print(f"Microphone: [{mic.index}] {mic.name}")

    speaker = find_speaker_device()
    if speaker:
        print(f"Speaker: [{speaker.index}] {speaker.name}")

    virtual_mic = find_virtual_mic_device()
    if virtual_mic:
        print(f"Virtual Mic: [{virtual_mic.index}] {virtual_mic.name}")
    else:
        print(
            "Virtual Mic: Not found (install BlackHole on macOS or VB-Audio on Windows)"
        )
    print()


async def test_connection(target_language: str) -> bool:
    """
    Test basic connection to Gemini API.

    Args:
        target_language: Target language code (e.g., "ja-JP")

    Returns:
        True if connection successful, False otherwise
    """
    print("\n=== Testing Gemini API Connection ===")

    try:
        # Create config
        lang = SupportedLanguage.from_code(target_language)
        config = GeminiConfig.from_env(target_language=lang)

        print(f"Target language: {config.language_display_name}")
        print(f"Model: {config.model}")

        # Create client and connect
        print("\nConnecting to Gemini API...")
        client = GeminiS2STClient(config)

        async with client:
            print("✓ Connection successful!")
            print(f"  State: {client.state.name}")
            print(f"  Connected: {client.is_connected}")

            # Wait a moment to ensure stable connection
            await asyncio.sleep(2)

            print("\n✓ API connection test passed!")
            return True

    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        return False


async def test_outgoing_translation(
    target_language: str, duration: int = 10
) -> bool:
    """
    Test outgoing translation: Mic -> Gemini -> Speakers.

    This tests translation without virtual mic (useful for development).

    Args:
        target_language: Target language code (e.g., "ja-JP")
        duration: Test duration in seconds

    Returns:
        True if test successful, False otherwise
    """
    print("\n=== Testing Outgoing Translation (Mic -> Speakers) ===")

    try:
        # Create config
        lang = SupportedLanguage.from_code(target_language)
        config = GeminiConfig.from_env(target_language=lang, enable_transcription=True)

        print(f"Target language: {config.language_display_name}")
        print(f"Duration: {duration} seconds")
        print("\nStarting in 3 seconds... Get ready to speak!")
        await asyncio.sleep(3)

        # Create client
        client = GeminiS2STClient(config)
        mic = MicrophoneCapture()
        speaker = SpeakerOutput()

        async with client:
            await mic.start()
            await speaker.start()

            print("\n✓ Recording started! Speak into your microphone...")
            print("  Your speech will be translated and played through speakers.")

            # Run for specified duration
            start_time = asyncio.get_running_loop().time()

            # Send task
            async def send_audio():
                async for chunk in mic.stream():
                    await client.send_audio(chunk.data)
                    if (
                        asyncio.get_running_loop().time() - start_time
                    ) > duration:
                        break

            # Receive task
            async def receive_audio():
                async for audio in client.receive_audio():
                    await speaker.write_chunk(audio)
                    if (
                        asyncio.get_running_loop().time() - start_time
                    ) > duration:
                        break

            # Run both concurrently
            await asyncio.gather(send_audio(), receive_audio())

            # Stop devices
            await mic.stop()
            await speaker.stop()

            # Show statistics
            print(f"\n✓ Test completed!")
            print(f"\nStatistics:")
            stats = client.stats
            print(f"  Chunks sent: {stats['chunks_sent']}")
            print(f"  Chunks received: {stats['chunks_received']}")
            print(f"  Bytes sent: {stats['bytes_sent']:,}")
            print(f"  Bytes received: {stats['bytes_received']:,}")
            print(f"  Duration: {stats['connection_duration']:.1f}s")

            # Token usage (estimates - S2ST preview is FREE)
            print(f"\nToken Usage (estimated):")
            print(f"  Audio sent: {stats['audio_seconds_sent']:.1f}s")
            print(f"  Audio received: {stats['audio_seconds_received']:.1f}s")
            print(f"  Input tokens: {stats['estimated_input_tokens']:,}")
            print(f"  Output tokens: {stats['estimated_output_tokens']:,}")
            print(f"  Total tokens: {stats['estimated_total_tokens']:,}")
            print(f"  Note: S2ST preview is currently FREE")

            # Show transcriptions if enabled
            input_trans, output_trans = client.get_transcriptions()
            if input_trans:
                print(f"\nInput transcription:")
                print(f"  {' '.join(input_trans)}")
            if output_trans:
                print(f"\nOutput transcription:")
                print(f"  {' '.join(output_trans)}")

            return True

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_full_pipeline(target_language: str, duration: int = 30) -> bool:
    """
    Test full translation pipeline: Mic -> Gemini -> Virtual Mic.

    Args:
        target_language: Target language code (e.g., "ja-JP")
        duration: Test duration in seconds

    Returns:
        True if test successful, False otherwise
    """
    print("\n=== Testing Full Translation Pipeline ===")

    try:
        # Check for virtual mic
        virtual_mic = find_virtual_mic_device()
        if not virtual_mic:
            print(
                "\n✗ Virtual microphone device not found. "
                "Please install BlackHole (macOS) or VB-Audio (Windows)."
            )
            return False

        # Create config
        lang = SupportedLanguage.from_code(target_language)
        config = GeminiConfig.from_env(target_language=lang)

        print(f"Target language: {config.language_display_name}")
        print(f"Virtual mic: {virtual_mic.name}")
        print(f"Duration: {duration} seconds")
        print("\nStarting in 3 seconds... Get ready to speak!")
        await asyncio.sleep(3)

        # Create pipeline
        pipeline = TranslationPipeline(config)

        async with pipeline:
            print("\n✓ Pipeline started! Speak into your microphone...")
            print(
                "  Translated audio will be sent to virtual mic for Zoom to capture."
            )

            # Start outgoing pipeline
            await pipeline.start_outgoing()

            # Run for specified duration
            await asyncio.sleep(duration)

            # Show statistics
            print(f"\n✓ Test completed!")
            print(f"\nPipeline Statistics:")
            stats = pipeline.stats
            print(f"  State: {stats['state']}")
            print(f"  Mode: {stats['mode']}")
            print(f"  Audio chunks captured: {stats['audio_chunks_captured']}")
            print(
                f"  Audio chunks sent to Gemini: {stats['audio_chunks_sent_to_gemini']}"
            )
            print(
                f"  Audio chunks received from Gemini: {stats['audio_chunks_received_from_gemini']}"
            )
            print(f"  Audio chunks played: {stats['audio_chunks_played']}")
            print(f"  Errors: {stats['errors_encountered']}")

            return True

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Gemini Speech-to-Speech Translation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--list-languages", action="store_true", help="List all supported languages"
    )
    parser.add_argument(
        "--list-devices", action="store_true", help="List all audio devices"
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test API connection only",
    )
    parser.add_argument(
        "--test-outgoing",
        action="store_true",
        help="Test outgoing translation (mic -> speakers)",
    )
    parser.add_argument(
        "--test-pipeline",
        action="store_true",
        help="Test full pipeline (mic -> virtual mic)",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="ja-JP",
        help="Target language code (default: ja-JP)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Test duration in seconds (default: 10)",
    )

    args = parser.parse_args()

    # List languages
    if args.list_languages:
        list_available_languages()
        return

    # List devices
    if args.list_devices:
        list_devices()
        return

    # Check GCP credentials for tests that need it
    if args.test_connection or args.test_outgoing or args.test_pipeline:
        if not check_gcp_credentials():
            sys.exit(1)

    # Run tests
    if args.test_connection:
        success = asyncio.run(test_connection(args.target))
        sys.exit(0 if success else 1)

    elif args.test_outgoing:
        success = asyncio.run(test_outgoing_translation(args.target, args.duration))
        sys.exit(0 if success else 1)

    elif args.test_pipeline:
        success = asyncio.run(test_full_pipeline(args.target, args.duration))
        sys.exit(0 if success else 1)

    else:
        # No test specified, show usage
        parser.print_help()
        print("\n=== Quick Start ===")
        print("1. List supported languages:")
        print("   python test_gemini_translation.py --list-languages")
        print("\n2. List audio devices:")
        print("   python test_gemini_translation.py --list-devices")
        print("\n3. Test API connection:")
        print("   python test_gemini_translation.py --test-connection --target ja-JP")
        print("\n4. Test outgoing translation (mic -> speakers):")
        print(
            "   python test_gemini_translation.py --test-outgoing --target es-ES --duration 10"
        )
        print("\n5. Test full pipeline (requires virtual audio device):")
        print(
            "   python test_gemini_translation.py --test-pipeline --target fr-FR --duration 30"
        )


if __name__ == "__main__":
    main()
