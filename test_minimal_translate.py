#!/usr/bin/env python3
"""
Minimal end-to-end translation test.

Bypasses the pipeline/client abstractions to isolate issues.
Mic -> Gemini Live API -> Speaker, with logging at every step.
"""

import asyncio
import os
import sys
from pathlib import Path

import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from google import genai
from google.genai import types
import pyaudio

# ── Config ──────────────────────────────────────────────
PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")
MODEL = os.environ.get("GEMINI_MODEL")
TARGET_LANG = "ja"  # Japanese
DURATION = 15  # seconds

MIC_RATE = 16000
SPEAKER_RATE = 24000
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1


async def main():
    print(f"Project:  {PROJECT}")
    print(f"Model:    {MODEL}")
    print(f"Target:   {TARGET_LANG}")
    print(f"Duration: {DURATION}s")

    if not PROJECT or not MODEL:
        print("ERROR: Set GOOGLE_CLOUD_PROJECT and GEMINI_MODEL in .env")
        return

    # ── Init Vertex AI client ───────────────────────────
    client = genai.Client(
        vertexai=True,
        project=PROJECT,
        location="us-central1",
    )
    print("✓ Client created")

    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(language_code=TARGET_LANG),
    )
    print("✓ Config created")

    # ── Init PyAudio ────────────────────────────────────
    pa = pyaudio.PyAudio()

    mic_stream = pa.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=MIC_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )
    print("✓ Mic opened (16kHz)")

    speaker_stream = pa.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SPEAKER_RATE,
        output=True,
        frames_per_buffer=CHUNK,
    )
    print("✓ Speaker opened (24kHz)")

    # ── Connect to Gemini ───────────────────────────────
    print("\nConnecting to Gemini Live API...")

    async with client.aio.live.connect(model=MODEL, config=config) as session:
        print("✓ Connected! Speak now...\n")

        chunks_sent = 0
        chunks_received = 0
        bytes_received = 0

        async def send_mic():
            nonlocal chunks_sent
            loop = asyncio.get_running_loop()
            while True:
                # Read mic in executor (blocking call)
                data = await loop.run_in_executor(
                    None, mic_stream.read, CHUNK, False
                )
                blob = types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                await session.send_realtime_input(audio=blob)
                chunks_sent += 1
                if chunks_sent % 50 == 0:
                    print(f"  → Sent {chunks_sent} chunks")

        async def receive_and_play():
            nonlocal chunks_received, bytes_received
            async for response in session.receive():
                # Check all possible response shapes
                sc = getattr(response, "server_content", None)
                if sc:
                    mt = getattr(sc, "model_turn", None)
                    if mt and mt.parts:
                        for part in mt.parts:
                            if part.inline_data:
                                audio = part.inline_data.data
                                chunks_received += 1
                                bytes_received += len(audio)
                                speaker_stream.write(audio)
                                if chunks_received % 10 == 0:
                                    print(f"  ← Received {chunks_received} chunks ({bytes_received:,} bytes)")
                            if part.text:
                                print(f"  [transcript] {part.text}")

        async def timeout_stop():
            await asyncio.sleep(DURATION)
            print(f"\n⏱ {DURATION}s elapsed — stopping...")

        # Run all three, stop when timeout fires
        send_task = asyncio.create_task(send_mic())
        recv_task = asyncio.create_task(receive_and_play())
        timeout_task = asyncio.create_task(timeout_stop())

        # Wait for timeout, then cancel others
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

    # ── Cleanup ─────────────────────────────────────────
    mic_stream.stop_stream()
    mic_stream.close()
    speaker_stream.stop_stream()
    speaker_stream.close()
    pa.terminate()

    print(f"\n{'='*40}")
    print(f"Chunks sent:     {chunks_sent}")
    print(f"Chunks received: {chunks_received}")
    print(f"Bytes received:  {bytes_received:,}")
    print(f"{'='*40}")

    if chunks_received == 0:
        print("\n⚠ No audio received from Gemini!")
        print("  Possible causes:")
        print("  - Model doesn't support S2ST with this config")
        print("  - Mic wasn't picking up speech")
        print("  - API needs enable_speech_to_speech_translation=True")


if __name__ == "__main__":
    asyncio.run(main())
