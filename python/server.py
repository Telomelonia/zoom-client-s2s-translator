#!/usr/bin/env python3
"""
Stdio JSON-lines server for Electron IPC.
Reads JSON commands from stdin, writes JSON events to stdout, logs to stderr.

Protocol:
  stdin:  {"cmd": "ping"}
  stdout: {"type": "pong"}

  stdin:  {"cmd": "list_devices"}
  stdout: {"type": "devices", "inputs": [...], "outputs": [...]}

  stdin:  {"cmd": "start", "mode": "upstream", "target": "ja", "mic_index": null, "speaker_index": null, "blackhole_index": null, "segment": 5}
  stdout: {"type": "started", "mode": "upstream", "target": "ja"}
  stdout: {"type": "status", "chunks_sent": 50, ...}  (every ~500ms)
  ...
  stdin:  {"cmd": "stop"}
  stdout: {"type": "stopped", ...}
"""

import asyncio
import json
import os
import sys
import threading
import queue
from pathlib import Path

import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from google import genai
from google.genai import types
import numpy as np
import pyaudio

# ── Constants ──────────────────────────────────────────
FORMAT = pyaudio.paInt16
CHUNK = 1024
GEMINI_INPUT_RATE = 16000
GEMINI_OUTPUT_RATE = 24000

LANG_NAMES = {
    "ja": "Japanese", "es": "Spanish", "fr": "French", "de": "German",
    "zh": "Chinese", "cmn": "Mandarin Chinese", "ko": "Korean",
    "pt": "Portuguese", "it": "Italian", "ru": "Russian", "ar": "Arabic",
    "hi": "Hindi", "en": "English", "nl": "Dutch", "sv": "Swedish",
    "pl": "Polish", "tr": "Turkish", "vi": "Vietnamese", "th": "Thai",
}


def log(msg: str):
    """Log to stderr (visible in Electron debug, not mixed with JSON protocol)."""
    print(msg, file=sys.stderr, flush=True)


def emit(obj: dict):
    """Write a JSON event to stdout."""
    print(json.dumps(obj), flush=True)


def translator_instruction(target_code: str) -> str:
    lang = LANG_NAMES.get(target_code, target_code)
    return (
        f"You are a live interpreter. Your ONLY job is to translate the user's speech into {lang}. "
        f"Output ONLY the {lang} translation. "
        "Do not add any commentary, explanation, or your own words. "
        "Do not greet or respond as an assistant. "
        "Just translate exactly what is said."
    )


def resample(data: bytes, from_rate: int, to_rate: int) -> bytes:
    if from_rate == to_rate:
        return data
    samples = np.frombuffer(data, dtype=np.int16).astype(np.float64)
    num_output = int(len(samples) * to_rate / from_rate)
    indices = np.linspace(0, len(samples) - 1, num_output)
    resampled = np.interp(indices, np.arange(len(samples)), samples)
    return resampled.astype(np.int16).tobytes()


def stereo_to_mono(data: bytes) -> bytes:
    samples = np.frombuffer(data, dtype=np.int16)
    stereo = samples.reshape(-1, 2).astype(np.float64)
    mono = stereo.mean(axis=1).astype(np.int16)
    return mono.tobytes()


# ── Device listing ──────────────────────────────────────
def get_devices() -> dict:
    pa = pyaudio.PyAudio()
    inputs = []
    outputs = []
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        entry = {"index": i, "name": info["name"]}
        if info["maxInputChannels"] > 0:
            inputs.append(entry)
        if info["maxOutputChannels"] > 0:
            outputs.append(entry)
    pa.terminate()
    return {"inputs": inputs, "outputs": outputs}


# ── Translation task ────────────────────────────────────
class TranslationSession:
    """Manages a single translation session (upstream or downstream)."""

    def __init__(self, mode: str, target: str, mic_index, speaker_index, blackhole_index, segment: float):
        self.mode = mode
        self.target = target
        self.mic_index = mic_index
        self.speaker_index = speaker_index
        self.blackhole_index = blackhole_index
        self.segment = segment
        self.chunks_sent = 0
        self.chunks_received = 0
        self.chunks_played = 0

    async def run(self):
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        model = os.environ.get("GEMINI_MODEL")

        if not project or not model:
            emit({"type": "error", "message": "GOOGLE_CLOUD_PROJECT and GEMINI_MODEL must be set in .env"})
            return

        pa = pyaudio.PyAudio()
        try:
            if self.mode == "upstream":
                await self._run_upstream(pa, project, model)
            elif self.mode == "downstream":
                await self._run_downstream(pa, project, model)
            else:
                emit({"type": "error", "message": f"Unknown mode: {self.mode}"})
        except asyncio.CancelledError:
            log("Translation cancelled")
        except Exception as e:
            log(f"Translation error: {e}")
            emit({"type": "error", "message": str(e)})
        finally:
            pa.terminate()
            emit({
                "type": "stopped",
                "chunks_sent": self.chunks_sent,
                "chunks_received": self.chunks_received,
                "chunks_played": self.chunks_played,
            })

    async def _cancel_and_wait(self, tasks: list[asyncio.Task], playback_queue: asyncio.Queue, out_stream):
        """Cancel all sub-tasks, wait for them, then drain remaining audio."""
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        while not playback_queue.empty():
            data = playback_queue.get_nowait()
            out_stream.write(data)
            self.chunks_played += 1

    async def _run_upstream(self, pa: pyaudio.PyAudio, project: str, model: str):
        """Mic → Gemini S2ST → BlackHole (or speakers if no BlackHole)."""
        log(f"  mic_index={self.mic_index}, speaker_index={self.speaker_index}, blackhole_index={self.blackhole_index}")
        mic_stream = pa.open(
            format=FORMAT, channels=1, rate=GEMINI_INPUT_RATE,
            input=True, input_device_index=self.mic_index,
            frames_per_buffer=CHUNK,
        )
        out_index = self.blackhole_index if self.blackhole_index is not None else self.speaker_index
        out_stream = pa.open(
            format=FORMAT, channels=1, rate=GEMINI_OUTPUT_RATE,
            output=True, output_device_index=out_index,
            frames_per_buffer=CHUNK,
        )

        try:
            playback_queue = asyncio.Queue()
            client = genai.Client(vertexai=True, project=project, location="us-central1")
            config = types.LiveConnectConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(language_code=self.target),
                system_instruction=types.Content(
                    parts=[types.Part(text=translator_instruction(self.target))]
                ),
                realtime_input_config=types.RealtimeInputConfig(
                    automatic_activity_detection=types.AutomaticActivityDetection(disabled=True),
                ),
            )

            playback_queue = asyncio.Queue()
            play_task = None
            status_task = None

            async def play_audio():
                loop = asyncio.get_running_loop()
                while True:
                    data = await playback_queue.get()
                    await loop.run_in_executor(None, out_stream.write, data)
                    self.chunks_played += 1

            async def emit_status():
                while True:
                    await asyncio.sleep(0.5)
                    emit({
                        "type": "status",
                        "chunks_sent": self.chunks_sent,
                        "chunks_received": self.chunks_received,
                        "chunks_played": self.chunks_played,
                        "backlog": playback_queue.qsize(),
                    })

            play_task = asyncio.create_task(play_audio())
            status_task = asyncio.create_task(emit_status())

            # Reconnect loop: new session per segment to avoid freeze after first response
            segment_num = 0
            loop = asyncio.get_running_loop()
            chunks_per_segment = int(GEMINI_INPUT_RATE / CHUNK * self.segment)

            try:
                while True:
                    segment_num += 1
                    log(f"  -> Segment {segment_num}: connecting...")
                    async with client.aio.live.connect(model=model, config=config) as session:
                        if segment_num == 1:
                            emit({"type": "started", "mode": self.mode, "target": self.target})
                        log(f"  -> Segment {segment_num}: sending {self.segment}s audio")

                        # Send one segment
                        await session.send_realtime_input(activity_start=types.ActivityStart())
                        for _ in range(chunks_per_segment):
                            data = await loop.run_in_executor(None, mic_stream.read, CHUNK, False)
                            blob = types.Blob(data=data, mime_type=f"audio/pcm;rate={GEMINI_INPUT_RATE}")
                            await session.send_realtime_input(audio=blob)
                            self.chunks_sent += 1
                        await session.send_realtime_input(activity_end=types.ActivityEnd())
                        log(f"  -> Segment {segment_num}: sent, waiting for response...")

                        # Receive all response audio until turn_complete
                        async for response in session.receive():
                            sc = getattr(response, "server_content", None)
                            if not sc:
                                continue
                            if getattr(sc, "turn_complete", False):
                                log(f"  <- Segment {segment_num}: turn complete (recv: {self.chunks_received})")
                                break
                            mt = getattr(sc, "model_turn", None)
                            if not mt or not mt.parts:
                                continue
                            for part in mt.parts:
                                if part.inline_data:
                                    await playback_queue.put(part.inline_data.data)
                                    self.chunks_received += 1
                    # Session closed, loop back to create a new one
            except asyncio.CancelledError:
                if play_task:
                    play_task.cancel()
                if status_task:
                    status_task.cancel()
                await asyncio.gather(play_task, status_task, return_exceptions=True)
                while not playback_queue.empty():
                    data = playback_queue.get_nowait()
                    out_stream.write(data)
                    self.chunks_played += 1
                raise
        finally:
            mic_stream.stop_stream()
            mic_stream.close()
            out_stream.stop_stream()
            out_stream.close()

    async def _run_downstream(self, pa: pyaudio.PyAudio, project: str, model: str):
        """BlackHole (Zoom audio) → Gemini S2ST → Speakers."""
        bh_index = self.blackhole_index
        if bh_index is None:
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if "blackhole" in info["name"].lower() and info["maxInputChannels"] > 0:
                    bh_index = i
                    break
        if bh_index is None:
            emit({"type": "error", "message": "BlackHole not found. Install with: brew install blackhole-2ch"})
            return

        bh_info = pa.get_device_info_by_index(bh_index)
        bh_channels = int(bh_info["maxInputChannels"]) if bh_info["maxInputChannels"] >= 2 else 1
        bh_stream = pa.open(
            format=FORMAT, channels=bh_channels, rate=GEMINI_OUTPUT_RATE,
            input=True, input_device_index=bh_index,
            frames_per_buffer=CHUNK,
        )
        speaker_stream = pa.open(
            format=FORMAT, channels=1, rate=GEMINI_OUTPUT_RATE,
            output=True, output_device_index=self.speaker_index,
            frames_per_buffer=CHUNK,
        )

        try:
            playback_queue = asyncio.Queue()
            client = genai.Client(vertexai=True, project=project, location="us-central1")
            config = types.LiveConnectConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(language_code=self.target),
                system_instruction=types.Content(
                    parts=[types.Part(text=translator_instruction(self.target))]
                ),
                realtime_input_config=types.RealtimeInputConfig(
                    automatic_activity_detection=types.AutomaticActivityDetection(disabled=True),
                ),
            )

            play_task = None
            status_task = None

            async def play_audio():
                loop = asyncio.get_running_loop()
                while True:
                    data = await playback_queue.get()
                    await loop.run_in_executor(None, speaker_stream.write, data)
                    self.chunks_played += 1

            async def emit_status():
                while True:
                    await asyncio.sleep(0.5)
                    emit({
                        "type": "status",
                        "chunks_sent": self.chunks_sent,
                        "chunks_received": self.chunks_received,
                        "chunks_played": self.chunks_played,
                        "backlog": playback_queue.qsize(),
                    })

            play_task = asyncio.create_task(play_audio())
            status_task = asyncio.create_task(emit_status())

            segment_num = 0
            loop = asyncio.get_running_loop()
            chunks_per_segment = int(GEMINI_INPUT_RATE / CHUNK * self.segment)

            try:
                while True:
                    segment_num += 1
                    log(f"  -> Segment {segment_num}: connecting...")
                    async with client.aio.live.connect(model=model, config=config) as session:
                        if segment_num == 1:
                            emit({"type": "started", "mode": self.mode, "target": self.target})

                        await session.send_realtime_input(activity_start=types.ActivityStart())
                        for _ in range(chunks_per_segment):
                            data = await loop.run_in_executor(None, bh_stream.read, CHUNK, False)
                            if bh_channels == 2:
                                data = stereo_to_mono(data)
                            data = resample(data, GEMINI_OUTPUT_RATE, GEMINI_INPUT_RATE)
                            blob = types.Blob(data=data, mime_type=f"audio/pcm;rate={GEMINI_INPUT_RATE}")
                            await session.send_realtime_input(audio=blob)
                            self.chunks_sent += 1
                        await session.send_realtime_input(activity_end=types.ActivityEnd())

                        async for response in session.receive():
                            sc = getattr(response, "server_content", None)
                            if not sc:
                                continue
                            if getattr(sc, "turn_complete", False):
                                break
                            mt = getattr(sc, "model_turn", None)
                            if not mt or not mt.parts:
                                continue
                            for part in mt.parts:
                                if part.inline_data:
                                    await playback_queue.put(part.inline_data.data)
                                    self.chunks_received += 1
            except asyncio.CancelledError:
                if play_task:
                    play_task.cancel()
                if status_task:
                    status_task.cancel()
                await asyncio.gather(play_task, status_task, return_exceptions=True)
                while not playback_queue.empty():
                    data = playback_queue.get_nowait()
                    speaker_stream.write(data)
                    self.chunks_played += 1
                raise
        finally:
            bh_stream.stop_stream()
            bh_stream.close()
            speaker_stream.stop_stream()
            speaker_stream.close()


# ── Main event loop ─────────────────────────────────────
def stdin_reader(q: queue.Queue):
    """Read stdin lines in a thread (blocking I/O)."""
    for line in sys.stdin:
        line = line.strip()
        if line:
            q.put(line)
    q.put(None)  # EOF


async def main():
    cmd_queue = queue.Queue()
    threading.Thread(target=stdin_reader, args=(cmd_queue,), daemon=True).start()

    emit({"type": "ready"})
    log("Python server ready")

    session: TranslationSession | None = None
    translation_task: asyncio.Task | None = None

    while True:
        try:
            raw = cmd_queue.get_nowait()
        except queue.Empty:
            await asyncio.sleep(0.05)
            continue

        if raw is None:
            log("stdin closed, exiting")
            break

        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            log(f"Bad JSON: {raw}")
            emit({"type": "error", "message": f"Invalid JSON: {raw}"})
            continue

        cmd = msg.get("cmd")
        log(f"cmd: {cmd}")

        if cmd == "ping":
            emit({"type": "pong"})

        elif cmd == "list_devices":
            devices = get_devices()
            emit({"type": "devices", **devices})

        elif cmd == "start":
            if translation_task and not translation_task.done():
                translation_task.cancel()
                try:
                    await translation_task
                except asyncio.CancelledError:
                    pass

            session = TranslationSession(
                mode=msg.get("mode", "upstream"),
                target=msg.get("target", "ja"),
                mic_index=msg.get("mic_index"),
                speaker_index=msg.get("speaker_index"),
                blackhole_index=msg.get("blackhole_index"),
                segment=msg.get("segment", 5),
            )
            translation_task = asyncio.create_task(session.run())

        elif cmd == "stop":
            if translation_task and not translation_task.done():
                translation_task.cancel()
                try:
                    await translation_task
                except asyncio.CancelledError:
                    pass
            else:
                emit({"type": "stopped", "chunks_sent": 0, "chunks_received": 0, "chunks_played": 0})

        else:
            emit({"type": "error", "message": f"Unknown command: {cmd}"})

    # Cleanup
    if translation_task and not translation_task.done():
        translation_task.cancel()
        try:
            await translation_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
