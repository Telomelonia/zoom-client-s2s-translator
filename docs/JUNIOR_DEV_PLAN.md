# Junior Developer Implementation Plan

> **Start Here!** This is your step-by-step guide to building the Zoom S2S Translator.
> Follow each task in order. Check the box when done.

## Progress Overview

| Phase | Status | Tasks |
|-------|--------|-------|
| 1. Project Setup | ✅ Complete | 5/5 |
| 2. Audio Capture | 🚀 In Progress | 0/4 |
| 3. Gemini Integration | Not Started | 0/2 |
| 4. Full Integration | Not Started | 0/6 |

**Next Task:** [Task 2.1: Implement Microphone Capture](#task-21-implement-microphone-capture--start-here)

---

## Phase 1: Project Setup ✅ COMPLETE

> **Status:** All tasks completed and code reviewed. Committed to main branch.

### Task 1.1: Create Electron Project Structure
**What:** Set up the Electron (frontend) folder structure

**Steps:**
```bash
# From project root
mkdir -p electron/src/main
mkdir -p electron/src/renderer
mkdir -p electron/src/preload
```

**Files to create:**

1. `electron/package.json`:
```json
{
  "name": "zoom-s2s-translator",
  "version": "0.1.0",
  "main": "dist/main/index.js",
  "scripts": {
    "dev": "vite",
    "build": "vite build && electron-builder",
    "start": "electron ."
  },
  "dependencies": {
    "electron-store": "^8.1.0"
  },
  "devDependencies": {
    "electron": "^28.0.0",
    "electron-builder": "^24.9.0",
    "vite": "^5.0.0",
    "vite-plugin-electron": "^0.15.0",
    "typescript": "^5.3.0",
    "@types/node": "^20.10.0"
  }
}
```

2. `electron/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src/**/*"]
}
```

3. `electron/src/main/index.ts`:
```typescript
import { app, BrowserWindow } from 'electron';
import path from 'path';

let mainWindow: BrowserWindow | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 400,
    height: 500,
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Load the renderer
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
```

4. `electron/src/preload/index.ts`:
```typescript
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('api', {
  // IPC methods will go here
  send: (channel: string, data: unknown) => ipcRenderer.send(channel, data),
  on: (channel: string, callback: (...args: unknown[]) => void) => {
    ipcRenderer.on(channel, (_event, ...args) => callback(...args));
  },
});
```

5. `electron/src/renderer/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Zoom S2S Translator</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      margin: 0;
      padding: 20px;
      background: #1a1a2e;
      color: #eee;
    }
    h1 { text-align: center; }
    .status { color: #4ade80; text-align: center; }
  </style>
</head>
<body>
  <h1>Zoom S2S Translator</h1>
  <p class="status">Electron is working!</p>
</body>
</html>
```

**Done when:**
- [x] All folders exist
- [x] All 5 files created
- [x] `cd electron && npm install` runs without errors

---

### Task 1.2: Create Python Project Structure
**What:** Set up the Python (backend) folder structure

**Steps:**
```bash
# From project root
mkdir -p python/src/audio
mkdir -p python/src/gemini
mkdir -p python/src/routing
mkdir -p python/tests
```

**Files to create:**

1. `python/requirements.txt`:
```
# Core
google-cloud-aiplatform>=1.38.0
google-generativeai>=0.8.0

# Audio
pyaudio>=0.2.14
sounddevice>=0.4.6
numpy>=1.26.0

# Async
websockets>=12.0

# Utilities
python-dotenv>=1.0.0
pydantic>=2.5.0

# Development
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

2. `python/pyproject.toml`:
```toml
[project]
name = "zoom-s2s-backend"
version = "0.1.0"
requires-python = ">=3.10"

[tool.ruff]
line-length = 100
target-version = "py310"
```

3. `python/src/__init__.py`:
```python
"""Zoom S2S Translator - Python Backend"""
```

4. `python/src/main.py`:
```python
"""Main entry point for the Python backend."""
import asyncio
import sys

async def main() -> None:
    """Main async entry point."""
    print("Python backend started!")
    print(f"Python version: {sys.version}")

    # Keep running (will be replaced with actual logic)
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
```

5. `python/src/audio/__init__.py`:
```python
"""Audio capture and playback modules."""
```

6. `python/src/gemini/__init__.py`:
```python
"""Gemini API integration modules."""
```

7. `python/src/routing/__init__.py`:
```python
"""Virtual audio routing modules."""
```

8. `python/tests/__init__.py`:
```python
"""Test modules."""
```

**Done when:**
- [x] All folders exist
- [x] All 8 files created
- [x] `cd python && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt` runs without errors

---

### Task 1.3: Create Environment Setup
**What:** Create environment configuration files

**Files to create:**

1. `.env.example` (in project root):
```bash
# Google Cloud / Gemini API
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GEMINI_MODEL=gemini-2.5-flash-s2st-exp-11-2025

# Debug mode
DEBUG=false
```

2. `scripts/dev.sh`:
```bash
#!/bin/bash
# Development startup script

echo "Starting Zoom S2S Translator (Development Mode)"

# Start Python backend
cd python
source venv/bin/activate
python src/main.py &
PYTHON_PID=$!

# Start Electron
cd ../electron
npm run dev &
ELECTRON_PID=$!

# Cleanup on exit
trap "kill $PYTHON_PID $ELECTRON_PID 2>/dev/null" EXIT

wait
```

3. Make it executable:
```bash
chmod +x scripts/dev.sh
```

**Done when:**
- [x] `.env.example` exists in root
- [x] `scripts/dev.sh` exists and is executable

---

### Task 1.4: Install BlackHole (macOS only)
**What:** Install virtual audio driver for routing audio to Zoom

**Steps:**
```bash
# Install via Homebrew
brew install blackhole-2ch
```

**Done when:**
- [ ] BlackHole appears in System Settings > Sound > Output devices *(user setup required)*
- [ ] BlackHole appears in System Settings > Sound > Input devices *(user setup required)*

> **Note:** Run `scripts/install-blackhole.sh` to install BlackHole on macOS.

---

### Task 1.5: Verify Everything Works
**What:** Test that the basic setup runs

**Steps:**
1. Test Python:
```bash
cd python
source venv/bin/activate
python src/main.py
# Should print "Python backend started!" - Ctrl+C to stop
```

2. Test Electron (requires vite config first - see note):
```bash
cd electron
npm run start
# Should open a window with "Zoom S2S Translator"
```

**Done when:**
- [x] Python starts without errors
- [x] Electron window opens

---

## Phase 2: Audio Capture 🚀 IN PROGRESS

> **Status:** Now active. Implement the audio capture modules.

### Task 2.1: Implement Microphone Capture ← START HERE
**What:** Create a class that captures audio from the microphone

**File to create:** `python/src/audio/microphone.py`

> **Note:** Use the constants from `python/src/audio/__init__.py` which are already defined:
> - `SAMPLE_RATE_MIC = 16000` (16kHz for Gemini API)
> - `CHANNELS = 1` (mono)
> - `CHUNK_SIZE = 1024` (frames per buffer)

```python
"""Microphone audio capture module."""
from __future__ import annotations

import pyaudio
from collections.abc import Generator

from . import SAMPLE_RATE_MIC, CHANNELS, CHUNK_SIZE


class MicrophoneCapture:
    """Captures audio from the microphone."""

    FORMAT = pyaudio.paInt16  # 16-bit PCM

    def __init__(self, device_index: int | None = None) -> None:
        self.device_index = device_index
        self._audio: pyaudio.PyAudio | None = None
        self._stream: pyaudio.Stream | None = None

    def start(self) -> None:
        """Start capturing audio."""
        self._audio = pyaudio.PyAudio()
        self._stream = self._audio.open(
            format=self.FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE_MIC,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=CHUNK_SIZE,
        )
        print(f"Microphone capture started (device: {self.device_index})")

    def read_chunk(self) -> bytes:
        """Read one chunk of audio data."""
        if self._stream is None:
            raise RuntimeError("Stream not started. Call start() first.")
        return self._stream.read(CHUNK_SIZE, exception_on_overflow=False)

    def stream_audio(self) -> Generator[bytes, None, None]:
        """Generator that yields audio chunks continuously."""
        while self._stream and self._stream.is_active():
            yield self.read_chunk()

    def stop(self) -> None:
        """Stop capturing audio and release resources."""
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        if self._audio:
            self._audio.terminate()
            self._audio = None
        print("Microphone capture stopped")

    def __enter__(self) -> MicrophoneCapture:
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


def list_input_devices() -> list[dict[str, int | str]]:
    """List all available input (microphone) devices."""
    audio = pyaudio.PyAudio()
    devices = []

    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            devices.append({
                "index": i,
                "name": info["name"],
                "channels": info["maxInputChannels"],
            })

    audio.terminate()
    return devices


# Test if run directly
if __name__ == "__main__":
    print("Available microphones:")
    for dev in list_input_devices():
        print(f"  [{dev['index']}] {dev['name']}")

    print("\nRecording 3 seconds...")
    with MicrophoneCapture() as mic:
        chunks = []
        for _ in range(int(SAMPLE_RATE_MIC / CHUNK_SIZE * 3)):  # 3 seconds
            chunks.append(mic.read_chunk())

    print(f"Recorded {len(chunks)} chunks ({len(chunks) * CHUNK_SIZE / SAMPLE_RATE_MIC:.1f}s)")
```

**Test it:**
```bash
cd python
source venv/bin/activate
python src/audio/microphone.py
```

**Done when:**
- [ ] Lists available microphones
- [ ] Records 3 seconds without errors
- [ ] Prints "Recorded X chunks"

---

### Task 2.2: Implement Speaker Output
**What:** Create a class that plays audio through speakers

**File to create:** `python/src/audio/speaker.py`

> **Note:** Use `SAMPLE_RATE_OUTPUT = 24000` from `__init__.py` for Gemini API output.

```python
"""Speaker audio output module."""
from __future__ import annotations

import threading
from queue import Empty, Queue

import pyaudio

from . import SAMPLE_RATE_OUTPUT, CHANNELS, CHUNK_SIZE


class SpeakerOutput:
    """Plays audio through speakers with buffered playback."""

    FORMAT = pyaudio.paInt16  # 16-bit PCM

    def __init__(self, device_index: int | None = None) -> None:
        self.device_index = device_index
        self._audio: pyaudio.PyAudio | None = None
        self._stream: pyaudio.Stream | None = None
        self._buffer: Queue[bytes] = Queue()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start audio playback."""
        self._audio = pyaudio.PyAudio()
        self._stream = self._audio.open(
            format=self.FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE_OUTPUT,
            output=True,
            output_device_index=self.device_index,
            frames_per_buffer=CHUNK_SIZE,
        )
        self._running = True
        self._thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._thread.start()
        print(f"Speaker output started (device: {self.device_index})")

    def _playback_loop(self) -> None:
        """Background thread that plays audio from buffer."""
        while self._running:
            try:
                chunk = self._buffer.get(timeout=0.1)
                if self._stream:
                    self._stream.write(chunk)
            except Empty:
                continue  # Queue timeout, keep running

    def play(self, audio_data: bytes) -> None:
        """Add audio data to playback buffer."""
        self._buffer.put(audio_data)

    def stop(self) -> None:
        """Stop audio playback and release resources."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        if self._audio:
            self._audio.terminate()
            self._audio = None
        print("Speaker output stopped")

    def __enter__(self) -> SpeakerOutput:
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


def list_output_devices() -> list[dict[str, int | str]]:
    """List all available output (speaker) devices."""
    audio = pyaudio.PyAudio()
    devices = []

    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info["maxOutputChannels"] > 0:
            devices.append({
                "index": i,
                "name": info["name"],
                "channels": info["maxOutputChannels"],
            })

    audio.terminate()
    return devices


# Test if run directly
if __name__ == "__main__":
    import math
    import struct
    import time

    print("Available speakers:")
    for dev in list_output_devices():
        print(f"  [{dev['index']}] {dev['name']}")

    print("\nPlaying test tone (440Hz for 2 seconds)...")

    with SpeakerOutput() as speaker:
        # Generate 440Hz sine wave
        duration = 2.0
        frequency = 440
        samples = int(SAMPLE_RATE_OUTPUT * duration)

        for i in range(0, samples, CHUNK_SIZE):
            chunk_samples = min(CHUNK_SIZE, samples - i)
            chunk = b""
            for j in range(chunk_samples):
                t = (i + j) / SAMPLE_RATE_OUTPUT
                value = int(16000 * math.sin(2 * math.pi * frequency * t))
                chunk += struct.pack("<h", value)
            speaker.play(chunk)

        time.sleep(2.5)  # Wait for playback to finish

    print("Done!")
```

**Test it:**
```bash
cd python
source venv/bin/activate
python src/audio/speaker.py
# Should hear a 440Hz beep for 2 seconds
```

**Done when:**
- [ ] Lists available speakers
- [ ] Plays a 440Hz tone
- [ ] No audio glitches or errors

---

### Task 2.3: Test Mic-to-Speaker Loopback
**What:** Verify audio pipeline by playing mic input through speakers

**File to create:** `python/src/audio/test_loopback.py`

> **Warning:** The sample rate mismatch (16kHz mic → 24kHz speaker) will cause pitch shift.
> This is expected for this test - the real Gemini pipeline outputs 24kHz audio.

```python
"""Test microphone to speaker loopback."""
from __future__ import annotations

import time

from .microphone import MicrophoneCapture, list_input_devices
from .speaker import SpeakerOutput, list_output_devices


def main() -> None:
    """Run loopback test."""
    print("=== Audio Loopback Test ===")
    print("This will play your microphone through your speakers.")
    print("⚠️  Wear headphones to avoid feedback!\n")

    print("Input devices:")
    for dev in list_input_devices():
        print(f"  [{dev['index']}] {dev['name']}")

    print("\nOutput devices:")
    for dev in list_output_devices():
        print(f"  [{dev['index']}] {dev['name']}")

    input("\nPress Enter to start (5 second test)...")

    with MicrophoneCapture() as mic, SpeakerOutput() as speaker:
        print("Loopback active - speak into mic!")

        start_time = time.time()
        while time.time() - start_time < 5:
            chunk = mic.read_chunk()
            # Note: Sample rate mismatch (16kHz -> 24kHz) will cause pitch shift
            # This is just a test - real pipeline will handle conversion
            speaker.play(chunk)

    print("Test complete!")


if __name__ == "__main__":
    main()
```

**Test it:**
```bash
cd python
source venv/bin/activate
python -m src.audio.test_loopback
# Use headphones! Should hear your voice (pitch shifted)
```

**Done when:**
- [ ] Can hear your voice through speakers
- [ ] No crashes or errors

---

### Task 2.4: Add System Audio Capture (Optional - for incoming Zoom audio)
**What:** Create a class that captures system audio (for translating incoming Zoom audio)

**File to create:** `python/src/audio/system_capture.py`

> **Note:** This uses the same pattern as MicrophoneCapture but at 24kHz (SAMPLE_RATE_SYSTEM).
> Requires BlackHole or similar virtual audio device to capture system audio.

```python
"""System audio capture module for capturing application audio."""
from __future__ import annotations

import pyaudio
from collections.abc import Generator

from . import SAMPLE_RATE_SYSTEM, CHANNELS, CHUNK_SIZE


class SystemAudioCapture:
    """Captures system audio (e.g., from Zoom) via virtual audio device."""

    FORMAT = pyaudio.paInt16  # 16-bit PCM

    def __init__(self, device_index: int | None = None) -> None:
        """
        Initialize system audio capture.

        Args:
            device_index: PyAudio device index for the virtual audio device
                         (e.g., BlackHole). If None, uses default input.
        """
        self.device_index = device_index
        self._audio: pyaudio.PyAudio | None = None
        self._stream: pyaudio.Stream | None = None

    def start(self) -> None:
        """Start capturing system audio."""
        self._audio = pyaudio.PyAudio()
        self._stream = self._audio.open(
            format=self.FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE_SYSTEM,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=CHUNK_SIZE,
        )
        print(f"System audio capture started (device: {self.device_index})")

    def read_chunk(self) -> bytes:
        """Read one chunk of audio data."""
        if self._stream is None:
            raise RuntimeError("Stream not started. Call start() first.")
        return self._stream.read(CHUNK_SIZE, exception_on_overflow=False)

    def stream_audio(self) -> Generator[bytes, None, None]:
        """Generator that yields audio chunks continuously."""
        while self._stream and self._stream.is_active():
            yield self.read_chunk()

    def stop(self) -> None:
        """Stop capturing audio and release resources."""
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        if self._audio:
            self._audio.terminate()
            self._audio = None
        print("System audio capture stopped")

    def __enter__(self) -> SystemAudioCapture:
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


def find_blackhole_device() -> int | None:
    """Find the BlackHole virtual audio device index."""
    audio = pyaudio.PyAudio()

    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if "blackhole" in info["name"].lower() and info["maxInputChannels"] > 0:
            audio.terminate()
            return i

    audio.terminate()
    return None


# Test if run directly
if __name__ == "__main__":
    from .microphone import list_input_devices

    print("Available input devices:")
    for dev in list_input_devices():
        print(f"  [{dev['index']}] {dev['name']}")

    blackhole_idx = find_blackhole_device()
    if blackhole_idx is not None:
        print(f"\n✅ Found BlackHole at index {blackhole_idx}")
    else:
        print("\n⚠️  BlackHole not found. Install it with: brew install blackhole-2ch")
```

**Test it:**
```bash
cd python
source venv/bin/activate
python -m src.audio.system_capture
```

**Done when:**
- [ ] Lists available devices
- [ ] Finds BlackHole device (if installed)

---

## Phase 3: Gemini API Integration

### Task 3.1: Create Gemini S2ST Client
**What:** Implement the WebSocket client for Gemini's speech-to-speech translation

**File to create:** `python/src/gemini/client.py`

```python
"""Gemini S2ST API client."""
import asyncio
import os
from typing import AsyncGenerator, Optional
from google import genai
from google.genai import types

class GeminiS2STClient:
    """Client for Gemini Speech-to-Speech Translation API."""

    MODEL = "gemini-2.5-flash-s2st-exp-11-2025"

    def __init__(self, target_language: str = "ja"):
        """
        Initialize the client.

        Args:
            target_language: Target language code (e.g., 'ja' for Japanese)
        """
        self.target_language = target_language
        self.client = genai.Client()
        self.session: Optional[genai.live.AsyncSession] = None

    async def connect(self) -> None:
        """Establish WebSocket connection to Gemini API."""
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                language_code=self.target_language
            ),
            enable_speech_to_speech_translation=True,
        )

        self.session = await self.client.aio.live.connect(
            model=self.MODEL,
            config=config,
        )
        print(f"Connected to Gemini S2ST (target: {self.target_language})")

    async def send_audio(self, audio_chunk: bytes) -> None:
        """Send audio chunk to the API."""
        if not self.session:
            raise RuntimeError("Not connected")

        await self.session.send(
            input=types.LiveClientRealtimeInput(
                media_chunks=[
                    types.Blob(data=audio_chunk, mime_type="audio/pcm")
                ]
            )
        )

    async def receive_audio(self) -> AsyncGenerator[bytes, None]:
        """Receive translated audio from the API."""
        if not self.session:
            raise RuntimeError("Not connected")

        async for response in self.session.receive():
            if response.data:
                yield response.data

    async def disconnect(self) -> None:
        """Close the connection."""
        if self.session:
            await self.session.close()
            self.session = None
        print("Disconnected from Gemini S2ST")


# Test if run directly
async def test():
    print("Testing Gemini S2ST connection...")
    print("(Make sure GOOGLE_APPLICATION_CREDENTIALS is set)")

    client = GeminiS2STClient(target_language="ja")

    try:
        await client.connect()
        print("Connection successful!")

        # Send a small test chunk (silence)
        test_chunk = b'\x00' * 1024
        await client.send_audio(test_chunk)
        print("Sent test audio chunk")

        await client.disconnect()
        print("Test passed!")

    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test())
```

**Before testing:**
1. Set up Google Cloud credentials
2. Enable Vertex AI API in your project
3. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

**Test it:**
```bash
cd python
source venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json
python src/gemini/client.py
```

**Done when:**
- [ ] Connection to Gemini API succeeds
- [ ] "Connection successful!" is printed
- [ ] No authentication errors

---

### Task 3.2: Create Translation Pipeline
**What:** Connect microphone → Gemini → speaker

**File to create:** `python/src/gemini/pipeline.py`

```python
"""Translation pipeline connecting audio input/output with Gemini."""
import asyncio
from typing import Optional

from ..audio.microphone import MicrophoneCapture
from ..audio.speaker import SpeakerOutput
from .client import GeminiS2STClient

class TranslationPipeline:
    """Bidirectional translation pipeline."""

    def __init__(
        self,
        source_language: str = "en",
        target_language: str = "ja",
        mic_device: Optional[int] = None,
        speaker_device: Optional[int] = None,
    ):
        self.source_language = source_language
        self.target_language = target_language

        self.mic = MicrophoneCapture(device_index=mic_device)
        self.speaker = SpeakerOutput(device_index=speaker_device)
        self.gemini = GeminiS2STClient(target_language=target_language)

        self._running = False

    async def start(self) -> None:
        """Start the translation pipeline."""
        print(f"Starting pipeline: {self.source_language} -> {self.target_language}")

        # Connect to Gemini
        await self.gemini.connect()

        # Start audio
        self.mic.start()
        self.speaker.start()

        self._running = True

        # Run send and receive concurrently
        await asyncio.gather(
            self._send_loop(),
            self._receive_loop(),
        )

    async def _send_loop(self) -> None:
        """Send microphone audio to Gemini."""
        while self._running:
            try:
                chunk = self.mic.read_chunk()
                await self.gemini.send_audio(chunk)
            except Exception as e:
                print(f"Send error: {e}")
                await asyncio.sleep(0.1)

    async def _receive_loop(self) -> None:
        """Receive translated audio from Gemini and play it."""
        try:
            async for audio_chunk in self.gemini.receive_audio():
                if not self._running:
                    break
                self.speaker.play(audio_chunk)
        except Exception as e:
            print(f"Receive error: {e}")

    async def stop(self) -> None:
        """Stop the translation pipeline."""
        self._running = False
        self.mic.stop()
        self.speaker.stop()
        await self.gemini.disconnect()
        print("Pipeline stopped")


# Test if run directly
async def main():
    print("=== Translation Pipeline Test ===")
    print("This will translate your speech from English to Japanese")
    print("Press Ctrl+C to stop\n")

    pipeline = TranslationPipeline(
        source_language="en",
        target_language="ja",
    )

    try:
        await pipeline.start()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        await pipeline.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

**Test it:**
```bash
cd python
source venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json
python -m src.gemini.pipeline
# Speak English, hear Japanese!
```

**Done when:**
- [ ] Can speak into microphone
- [ ] Hear translated audio in target language
- [ ] No crashes when running for 30+ seconds

---

## Phase 4: Full Integration (Next Steps)

After completing Phases 1-3, you'll have:
- Working Electron shell
- Python audio capture/playback
- Gemini translation working

**Remaining tasks (with senior developer guidance):**
1. Implement Electron ↔ Python IPC
2. Build the UI components
3. Add system audio capture (for incoming Zoom audio)
4. Add virtual microphone routing (for outgoing to Zoom)
5. Error handling and stability
6. Packaging for distribution

---

## Quick Reference

### Run Commands
```bash
# Start both Electron + Python (recommended)
./scripts/dev.sh

# Start Python backend only
cd python && source venv/bin/activate && python src/main.py

# Start Electron only
cd electron && npm run dev

# Run microphone test
cd python && source venv/bin/activate && python -m src.audio.microphone

# Run speaker test
cd python && source venv/bin/activate && python -m src.audio.speaker

# Run audio loopback test
cd python && source venv/bin/activate && python -m src.audio.test_loopback

# Run translation test (requires Gemini API credentials)
cd python && source venv/bin/activate && python -m src.gemini.pipeline
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| PyAudio install fails | `brew install portaudio` then `pip install pyaudio` |
| No microphone permission | System Settings > Privacy > Microphone > Enable for Terminal |
| Gemini auth error | Check `GOOGLE_APPLICATION_CREDENTIALS` is set correctly |
| BlackHole not appearing | Restart your Mac after installation |

---

**Questions?** Ask the senior developer for help!
