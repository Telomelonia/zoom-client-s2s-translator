#!/usr/bin/env python3
"""
Bidirectional Zoom translator using Gemini Live S2ST.

Two modes:
  upstream   — Your mic (English) → Gemini → BlackHole (Japanese to Zoom)
  downstream — BlackHole (Zoom audio) → Gemini → Your speakers (English)

Usage:
  python3 translate.py upstream                # Mic → Japanese → BlackHole
  python3 translate.py downstream              # BlackHole → English → Speakers
  python3 translate.py upstream --target ja --duration 60
  python3 translate.py downstream --target es
"""

import argparse
import asyncio
import os
import struct
import sys
from pathlib import Path

import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from google import genai
from google.genai import types
import numpy as np
import pyaudio

# ── Constants ──────────────────────────────────────────
FORMAT = pyaudio.paInt16
CHUNK = 1024
GEMINI_INPUT_RATE = 16000   # Gemini expects 16kHz input
GEMINI_OUTPUT_RATE = 24000  # Gemini produces 24kHz output


def find_blackhole(pa: pyaudio.PyAudio) -> dict | None:
    """Scan PyAudio devices for BlackHole."""
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if "blackhole" in info["name"].lower():
            return info
    return None


def list_devices(pa: pyaudio.PyAudio):
    """Print all audio devices for debugging."""
    print("\nAudio devices:")
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        direction = []
        if info["maxInputChannels"] > 0:
            direction.append("IN")
        if info["maxOutputChannels"] > 0:
            direction.append("OUT")
        print(f"  [{i}] {info['name']} ({'/'.join(direction)})")
    print()


def resample(data: bytes, from_rate: int, to_rate: int) -> bytes:
    """Resample 16-bit PCM audio between sample rates."""
    if from_rate == to_rate:
        return data
    samples = np.frombuffer(data, dtype=np.int16).astype(np.float64)
    num_output = int(len(samples) * to_rate / from_rate)
    # Linear interpolation resampling
    indices = np.linspace(0, len(samples) - 1, num_output)
    resampled = np.interp(indices, np.arange(len(samples)), samples)
    return resampled.astype(np.int16).tobytes()


def stereo_to_mono(data: bytes) -> bytes:
    """Average stereo 16-bit PCM to mono."""
    samples = np.frombuffer(data, dtype=np.int16)
    # Reshape to (N, 2) and average channels
    stereo = samples.reshape(-1, 2).astype(np.float64)
    mono = stereo.mean(axis=1).astype(np.int16)
    return mono.tobytes()


async def run_upstream(args):
    """Mic → Gemini S2ST → BlackHole (for Zoom to pick up)."""
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    model = os.environ.get("GEMINI_MODEL")
    target = args.target or "ja"

    print(f"Mode:     UPSTREAM (your voice → translated to Zoom)")
    print(f"Project:  {project}")
    print(f"Model:    {model}")
    print(f"Target:   {target}")
    print(f"Duration: {args.duration}s")

    if not project or not model:
        print("ERROR: Set GOOGLE_CLOUD_PROJECT and GEMINI_MODEL in .env")
        return

    pa = pyaudio.PyAudio()

    # Find BlackHole for output
    if args.blackhole_index is not None:
        bh_index = args.blackhole_index
        bh_info = pa.get_device_info_by_index(bh_index)
        print(f"BlackHole (override): [{bh_index}] {bh_info['name']}")
    else:
        bh_info = find_blackhole(pa)
        if not bh_info:
            print("ERROR: BlackHole not found. Install with: brew install blackhole-2ch")
            list_devices(pa)
            pa.terminate()
            return
        bh_index = bh_info["index"]
        print(f"BlackHole: [{bh_index}] {bh_info['name']}")

    # Open mic input
    mic_index = args.mic_index
    if mic_index is not None:
        mic_info = pa.get_device_info_by_index(mic_index)
        print(f"Mic (override): [{mic_index}] {mic_info['name']}")
    else:
        mic_index = None  # PyAudio default
        print("Mic: system default")

    mic_stream = pa.open(
        format=FORMAT,
        channels=1,
        rate=GEMINI_INPUT_RATE,
        input=True,
        input_device_index=mic_index,
        frames_per_buffer=CHUNK,
    )
    print(f"  Mic opened (16kHz mono)")

    # Open BlackHole output at 24kHz (Gemini output rate)
    bh_stream = pa.open(
        format=FORMAT,
        channels=1,
        rate=GEMINI_OUTPUT_RATE,
        output=True,
        output_device_index=bh_index,
        frames_per_buffer=CHUNK,
    )
    print(f"  BlackHole output opened (24kHz mono)")

    # Connect to Gemini
    client = genai.Client(
        vertexai=True,
        project=project,
        location="us-central1",
    )
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(language_code=target),
    )

    print(f"\nConnecting to Gemini Live API...")
    async with client.aio.live.connect(model=model, config=config) as session:
        print(f"Connected! Speak now...\n")

        chunks_sent = 0
        chunks_received = 0

        async def send_mic():
            nonlocal chunks_sent
            loop = asyncio.get_running_loop()
            while True:
                data = await loop.run_in_executor(
                    None, mic_stream.read, CHUNK, False
                )
                blob = types.Blob(data=data, mime_type=f"audio/pcm;rate={GEMINI_INPUT_RATE}")
                await session.send_realtime_input(audio=blob)
                chunks_sent += 1
                if chunks_sent % 50 == 0:
                    print(f"  -> Sent {chunks_sent} chunks")

        async def receive_and_play():
            nonlocal chunks_received
            async for response in session.receive():
                sc = getattr(response, "server_content", None)
                if sc:
                    mt = getattr(sc, "model_turn", None)
                    if mt and mt.parts:
                        for part in mt.parts:
                            if part.inline_data:
                                bh_stream.write(part.inline_data.data)
                                chunks_received += 1
                                if chunks_received % 10 == 0:
                                    print(f"  <- Received {chunks_received} chunks")

        async def timeout_stop():
            await asyncio.sleep(args.duration)
            print(f"\n{args.duration}s elapsed - stopping...")

        send_task = asyncio.create_task(send_mic())
        recv_task = asyncio.create_task(receive_and_play())
        timeout_task = asyncio.create_task(timeout_stop())

        await timeout_task
        send_task.cancel()
        recv_task.cancel()
        try:
            await send_task
        except asyncio.CancelledError:
            pass
        try:
            await recv_task
        except asyncio.CancelledError:
            pass

    mic_stream.stop_stream()
    mic_stream.close()
    bh_stream.stop_stream()
    bh_stream.close()
    pa.terminate()

    print(f"\nUpstream complete: sent={chunks_sent}, received={chunks_received}")


async def run_downstream(args):
    """BlackHole (Zoom audio) → Gemini S2ST → Your speakers."""
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    model = os.environ.get("GEMINI_MODEL")
    target = args.target or "en"

    print(f"Mode:     DOWNSTREAM (Zoom audio → translated to your speakers)")
    print(f"Project:  {project}")
    print(f"Model:    {model}")
    print(f"Target:   {target}")
    print(f"Duration: {args.duration}s")

    if not project or not model:
        print("ERROR: Set GOOGLE_CLOUD_PROJECT and GEMINI_MODEL in .env")
        return

    pa = pyaudio.PyAudio()

    # Find BlackHole for input
    if args.blackhole_index is not None:
        bh_index = args.blackhole_index
        bh_info = pa.get_device_info_by_index(bh_index)
        print(f"BlackHole (override): [{bh_index}] {bh_info['name']}")
    else:
        bh_info = find_blackhole(pa)
        if not bh_info:
            print("ERROR: BlackHole not found. Install with: brew install blackhole-2ch")
            list_devices(pa)
            pa.terminate()
            return
        bh_index = bh_info["index"]
        print(f"BlackHole: [{bh_index}] {bh_info['name']}")

    # BlackHole captures stereo at 24kHz (or whatever rate Zoom outputs)
    bh_channels = int(bh_info["maxInputChannels"]) if bh_info["maxInputChannels"] >= 2 else 1
    bh_capture_rate = GEMINI_OUTPUT_RATE  # 24kHz — typical for BlackHole

    bh_stream = pa.open(
        format=FORMAT,
        channels=bh_channels,
        rate=bh_capture_rate,
        input=True,
        input_device_index=bh_index,
        frames_per_buffer=CHUNK,
    )
    print(f"  BlackHole input opened ({bh_capture_rate}Hz, {bh_channels}ch)")

    # Open speakers for output
    speaker_index = args.speaker_index
    if speaker_index is not None:
        spk_info = pa.get_device_info_by_index(speaker_index)
        print(f"Speaker (override): [{speaker_index}] {spk_info['name']}")
    else:
        speaker_index = None  # PyAudio default
        print("Speaker: system default")

    speaker_stream = pa.open(
        format=FORMAT,
        channels=1,
        rate=GEMINI_OUTPUT_RATE,
        output=True,
        output_device_index=speaker_index,
        frames_per_buffer=CHUNK,
    )
    print(f"  Speaker output opened (24kHz mono)")

    # Connect to Gemini
    client = genai.Client(
        vertexai=True,
        project=project,
        location="us-central1",
    )
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(language_code=target),
    )

    print(f"\nConnecting to Gemini Live API...")
    async with client.aio.live.connect(model=model, config=config) as session:
        print(f"Connected! Listening to BlackHole...\n")

        chunks_sent = 0
        chunks_received = 0

        async def send_blackhole():
            nonlocal chunks_sent
            loop = asyncio.get_running_loop()
            while True:
                data = await loop.run_in_executor(
                    None, bh_stream.read, CHUNK, False
                )
                # Convert stereo to mono if needed
                if bh_channels == 2:
                    data = stereo_to_mono(data)
                # Resample 24kHz → 16kHz for Gemini
                if bh_capture_rate != GEMINI_INPUT_RATE:
                    data = resample(data, bh_capture_rate, GEMINI_INPUT_RATE)
                blob = types.Blob(data=data, mime_type=f"audio/pcm;rate={GEMINI_INPUT_RATE}")
                await session.send_realtime_input(audio=blob)
                chunks_sent += 1
                if chunks_sent % 50 == 0:
                    print(f"  -> Sent {chunks_sent} chunks")

        async def receive_and_play():
            nonlocal chunks_received
            async for response in session.receive():
                sc = getattr(response, "server_content", None)
                if sc:
                    mt = getattr(sc, "model_turn", None)
                    if mt and mt.parts:
                        for part in mt.parts:
                            if part.inline_data:
                                speaker_stream.write(part.inline_data.data)
                                chunks_received += 1
                                if chunks_received % 10 == 0:
                                    print(f"  <- Received {chunks_received} chunks")

        async def timeout_stop():
            await asyncio.sleep(args.duration)
            print(f"\n{args.duration}s elapsed - stopping...")

        send_task = asyncio.create_task(send_blackhole())
        recv_task = asyncio.create_task(receive_and_play())
        timeout_task = asyncio.create_task(timeout_stop())

        await timeout_task
        send_task.cancel()
        recv_task.cancel()
        try:
            await send_task
        except asyncio.CancelledError:
            pass
        try:
            await recv_task
        except asyncio.CancelledError:
            pass

    bh_stream.stop_stream()
    bh_stream.close()
    speaker_stream.stop_stream()
    speaker_stream.close()
    pa.terminate()

    print(f"\nDownstream complete: sent={chunks_sent}, received={chunks_received}")


def main():
    parser = argparse.ArgumentParser(
        description="Bidirectional Zoom translator using Gemini S2ST",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 translate.py upstream               # Mic → Japanese → BlackHole
  python3 translate.py downstream             # BlackHole → English → Speakers
  python3 translate.py upstream --target ja --duration 60
  python3 translate.py downstream --target es

Prerequisites:
  1. brew install blackhole-2ch
  2. For upstream: Zoom → Audio → Microphone = "BlackHole 2ch"
  3. For downstream: Zoom → Audio → Speaker = "BlackHole 2ch"
        """,
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["upstream", "downstream"],
        help="upstream: mic→Gemini→BlackHole | downstream: BlackHole→Gemini→speakers",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="Target language code (default: ja for upstream, en for downstream)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duration in seconds (default: 60)",
    )
    parser.add_argument(
        "--mic-index",
        type=int,
        default=None,
        help="Override mic device index",
    )
    parser.add_argument(
        "--speaker-index",
        type=int,
        default=None,
        help="Override speaker device index",
    )
    parser.add_argument(
        "--blackhole-index",
        type=int,
        default=None,
        help="Override BlackHole device index",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List all audio devices and exit",
    )

    args = parser.parse_args()

    if args.list_devices:
        pa = pyaudio.PyAudio()
        list_devices(pa)
        pa.terminate()
        return

    if not args.mode:
        parser.error("the following arguments are required: mode")

    if args.mode == "upstream":
        asyncio.run(run_upstream(args))
    else:
        asyncio.run(run_downstream(args))


if __name__ == "__main__":
    main()
