# Junior Developer Implementation Plan

> **Start Here!** This is your step-by-step guide to building the Zoom S2S Translator.
> Follow each task in order. Check the box when done.

## Progress Overview

| Phase | Status | Tasks |
|-------|--------|-------|
| 1. Project Setup | ✅ Complete | 5/5 |
| 2A. Audio Capture | ✅ Complete | 4/4 |
| 2B. Audio Playback | ✅ Complete (Submitted for Review) | 4/4 |
| 3. Gemini Integration | Not Started | 0/2 |
| 4. Full Integration | Not Started | 0/6 |

**Current Status:** Phase 2B submitted for review (REVIEW-2026-01-19-001)
**Next Task:** Awaiting Senior Developer review and approval

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

## Phase 2A: Audio Capture ✅ COMPLETE

> **Status:** All tasks completed and committed. See commit fd4334e.

### Task 2.1: Implement Microphone Capture ✅ COMPLETE
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

## Phase 2B: Audio Playback ✅ COMPLETE (Submitted for Review)

> **Status:** Implementation complete. Submitted as REVIEW-2026-01-19-001.
> **CRITICAL CORRECTION APPLIED:** Used `queue.Queue` instead of `asyncio.Queue` for thread-safe PyAudio callbacks.
> **Reference:** Implementation follows exact patterns from `python/src/audio/capture.py`.

### Task 2B.1: Implement Speaker Output ← START HERE
**What:** Create a class that plays translated audio through speakers

**File to create:** `python/src/audio/playback.py`

> **Important:** Follow the EXACT same patterns as `capture.py`:
> - Use PlaybackState enum (matching CaptureState pattern)
> - Use async queues for audio data
> - Use PyAudio callback mode for low latency
> - Include statistics tracking
> - Support context managers

```python
"""
Audio playback module.

Provides classes for playing audio to speakers and virtual microphone devices.
Uses PyAudio with async queues for non-blocking real-time streaming.
"""

import asyncio
import logging
from typing import Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum, auto

import pyaudio
import numpy as np

from . import (
    SAMPLE_RATE_OUTPUT,
    CHANNELS,
    CHUNK_SIZE,
    BIT_DEPTH,
)

logger = logging.getLogger(__name__)


class PlaybackState(Enum):
    """Audio playback state."""

    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    ERROR = auto()


class AudioPlaybackError(Exception):
    """Base exception for audio playback errors."""

    pass


class PlaybackDeviceError(AudioPlaybackError):
    """Playback device not found or unavailable."""

    pass


class PlaybackStreamError(AudioPlaybackError):
    """Error during audio playback streaming."""

    pass


class BasePlaybackDevice:
    """
    Base class for audio playback devices.

    Provides common functionality for both speaker and virtual mic output.
    Uses callback mode for minimal latency and async queues for integration.
    """

    def __init__(
        self,
        sample_rate: int,
        chunk_size: int = CHUNK_SIZE,
        channels: int = CHANNELS,
        device_index: Optional[int] = None,
    ):
        """
        Initialize audio playback device.

        Args:
            sample_rate: Audio sample rate in Hz
            chunk_size: Number of frames per buffer
            channels: Number of audio channels (1=mono, 2=stereo)
            device_index: PyAudio device index (None = default device)
        """
        self._sample_rate = sample_rate
        self._chunk_size = chunk_size
        self._channels = channels
        self._device_index = device_index

        self._pyaudio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._state = PlaybackState.STOPPED

        # Async queue for audio data to play
        self._queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=100)

        # Event loop reference for callback thread
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Statistics
        self._chunks_played = 0
        self._bytes_played = 0
        self._underruns = 0

        # Silence buffer for underruns
        self._silence = bytes(chunk_size * channels * (BIT_DEPTH // 8))

    @property
    def state(self) -> PlaybackState:
        """Current playback state."""
        return self._state

    @property
    def sample_rate(self) -> int:
        """Audio sample rate in Hz."""
        return self._sample_rate

    @property
    def is_running(self) -> bool:
        """Check if playback is currently running."""
        return self._state == PlaybackState.RUNNING

    @property
    def stats(self) -> dict:
        """Get playback statistics."""
        return {
            "chunks_played": self._chunks_played,
            "bytes_played": self._bytes_played,
            "underruns": self._underruns,
            "queue_size": self._queue.qsize(),
        }

    def _audio_callback(
        self,
        in_data: bytes,
        frame_count: int,
        time_info: dict,
        status_flags: int,
    ) -> tuple[bytes, int]:
        """
        PyAudio callback executed in separate thread.

        This is called by PyAudio when it needs more audio data to play.
        We need to return data quickly to avoid audio glitches.

        Args:
            in_data: Not used for output streams
            frame_count: Number of frames requested
            time_info: Timing information from PortAudio
            status_flags: Stream status flags

        Returns:
            Tuple of (audio_data, continue_flag)
        """
        # Check for output underflow (buffer underrun)
        if status_flags & pyaudio.paOutputUnderflow:
            self._underruns += 1
            logger.warning("Audio output underflow detected (buffer underrun)")

        try:
            # Try to get audio from queue without blocking
            try:
                audio_data = self._queue.get_nowait()
                self._chunks_played += 1
                self._bytes_played += len(audio_data)
            except asyncio.QueueEmpty:
                # No data available, play silence
                audio_data = self._silence
                self._underruns += 1

        except Exception as e:
            logger.error(f"Error in playback callback: {e}")
            audio_data = self._silence

        return (audio_data, pyaudio.paContinue)

    async def start(self) -> None:
        """
        Start audio playback.

        Raises:
            PlaybackDeviceError: If device is not available
            PlaybackStreamError: If stream cannot be started
        """
        if self._state != PlaybackState.STOPPED:
            raise PlaybackStreamError(f"Cannot start: already in {self._state} state")

        self._state = PlaybackState.STARTING
        self._loop = asyncio.get_running_loop()

        try:
            # Initialize PyAudio
            self._pyaudio = pyaudio.PyAudio()

            # Validate device
            if self._device_index is not None:
                try:
                    device_info = self._pyaudio.get_device_info_by_index(
                        self._device_index
                    )
                    logger.info(f"Using audio device: {device_info['name']}")
                except Exception as e:
                    raise PlaybackDeviceError(f"Invalid device index: {e}")

            # Open audio stream in callback mode
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,  # 16-bit PCM
                channels=self._channels,
                rate=self._sample_rate,
                output=True,
                output_device_index=self._device_index,
                frames_per_buffer=self._chunk_size,
                stream_callback=self._audio_callback,
                start=False,  # We'll start manually
            )

            # Start the stream
            self._stream.start_stream()
            self._state = PlaybackState.RUNNING

            logger.info(
                f"Audio playback started: {self._sample_rate}Hz, "
                f"{self._channels}ch, {self._chunk_size} frames"
            )

        except Exception as e:
            self._state = PlaybackState.ERROR
            await self._cleanup()
            raise PlaybackStreamError(f"Failed to start audio stream: {e}")

    async def stop(self) -> None:
        """
        Stop audio playback gracefully.

        This is idempotent - calling multiple times is safe.
        """
        if self._state == PlaybackState.STOPPED:
            return

        self._state = PlaybackState.STOPPING
        logger.info("Stopping audio playback...")

        await self._cleanup()

        self._state = PlaybackState.STOPPED
        logger.info(f"Audio playback stopped. Stats: {self.stats}")

    async def _cleanup(self) -> None:
        """Clean up PyAudio resources."""
        try:
            if self._stream:
                if self._stream.is_active():
                    self._stream.stop_stream()
                self._stream.close()
                self._stream = None

            if self._pyaudio:
                self._pyaudio.terminate()
                self._pyaudio = None

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def write_chunk(self, audio_data: bytes, timeout: Optional[float] = None) -> None:
        """
        Write audio data to playback queue.

        Args:
            audio_data: Raw PCM audio bytes to play
            timeout: Maximum time to wait if queue is full (None = wait forever)

        Raises:
            asyncio.TimeoutError: If timeout expires
            PlaybackStreamError: If playback is not running
        """
        if self._state != PlaybackState.RUNNING:
            raise PlaybackStreamError("Cannot write: playback is not running")

        if timeout:
            await asyncio.wait_for(self._queue.put(audio_data), timeout=timeout)
        else:
            await self._queue.put(audio_data)

    def write_chunk_nowait(self, audio_data: bytes) -> bool:
        """
        Write audio data to playback queue without blocking.

        Args:
            audio_data: Raw PCM audio bytes to play

        Returns:
            True if data was queued, False if queue was full
        """
        if self._state != PlaybackState.RUNNING:
            return False

        try:
            self._queue.put_nowait(audio_data)
            return True
        except asyncio.QueueFull:
            logger.warning("Playback queue full, dropping chunk")
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


class SpeakerOutput(BasePlaybackDevice):
    """
    Plays audio through physical speakers.

    Optimized for playing translated speech from Gemini S2ST API:
    - 24kHz sample rate (Gemini API output format)
    - 16-bit PCM format
    - Mono channel
    - 1024 frame chunks for low latency

    Example:
        ```python
        async with SpeakerOutput() as speaker:
            while True:
                translated_audio = await get_from_gemini()
                await speaker.write_chunk(translated_audio)
        ```
    """

    def __init__(
        self,
        device_index: Optional[int] = None,
        sample_rate: int = SAMPLE_RATE_OUTPUT,
        chunk_size: int = CHUNK_SIZE,
    ):
        """
        Initialize speaker output.

        Args:
            device_index: PyAudio device index (None = default speakers)
            sample_rate: Sample rate in Hz (default: 24kHz for Gemini output)
            chunk_size: Buffer size in frames (default: 1024)
        """
        super().__init__(
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            channels=CHANNELS,
            device_index=device_index,
        )
        logger.info("SpeakerOutput initialized")


class VirtualMicOutput(BasePlaybackDevice):
    """
    Routes audio to a virtual microphone device.

    Used to send translated audio INTO Zoom calls via a virtual audio device
    (BlackHole on macOS, VB-Audio Cable on Windows).

    The virtual mic device must be:
    1. Installed on the system (BlackHole, VB-Audio, etc.)
    2. Selected as the input device in Zoom

    Example:
        ```python
        # Find BlackHole device index first
        device_idx = find_virtual_mic_device()

        async with VirtualMicOutput(device_index=device_idx) as virtual_mic:
            while True:
                translated_audio = await get_from_gemini()
                await virtual_mic.write_chunk(translated_audio)
        ```
    """

    def __init__(
        self,
        device_index: int,
        sample_rate: int = SAMPLE_RATE_OUTPUT,
        chunk_size: int = CHUNK_SIZE,
    ):
        """
        Initialize virtual microphone output.

        Args:
            device_index: PyAudio device index for virtual audio device (required)
            sample_rate: Sample rate in Hz (default: 24kHz)
            chunk_size: Buffer size in frames (default: 1024)
        """
        super().__init__(
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            channels=CHANNELS,
            device_index=device_index,
        )
        logger.info("VirtualMicOutput initialized")
```

**Done when:**
- [ ] File created at `python/src/audio/playback.py`
- [ ] SpeakerOutput class implemented
- [ ] VirtualMicOutput class implemented
- [ ] All code has type hints and docstrings

---

### Task 2B.2: Add Output Device Convenience Functions
**What:** Add helper functions to find speaker and virtual mic devices

**File to update:** `python/src/audio/devices.py`

Add these functions after the existing `find_loopback_device()` function:

```python
def find_speaker_device(name: Optional[str] = None) -> Optional[AudioDevice]:
    """
    Find a speaker (output) device.

    Args:
        name: Device name to search for (None = default output device)

    Returns:
        AudioDevice if found, None otherwise

    Example:
        ```python
        speaker = find_speaker_device()
        if speaker:
            print(f"Default speaker: {speaker.name}")
        ```
    """
    with AudioDeviceManager() as manager:
        if name:
            device = manager.get_device_by_name(name)
            if device and device.is_output_device:
                return device
            return None
        else:
            return manager.get_default_output_device()


def find_virtual_mic_device() -> Optional[AudioDevice]:
    """
    Find a virtual audio device suitable for routing audio to Zoom.

    This looks for virtual output devices (BlackHole, VB-Audio, etc.)
    that can be selected as an input device in Zoom.

    Returns:
        AudioDevice if found, None otherwise

    Example:
        ```python
        virtual_mic = find_virtual_mic_device()
        if virtual_mic:
            print(f"Use device index {virtual_mic.index} for VirtualMicOutput")
        ```
    """
    with AudioDeviceManager() as manager:
        # Look for virtual devices that support output
        # (output from our app = input for other apps like Zoom)

        # Try BlackHole first (macOS)
        device = manager.get_device_by_name("blackhole")
        if device and device.is_output_device:
            return device

        # Try VB-Audio (Windows)
        device = manager.get_device_by_name("cable input")
        if device and device.is_output_device:
            return device

        device = manager.get_device_by_name("vb-audio")
        if device and device.is_output_device:
            return device

        # Return first virtual output device found
        for device in manager.get_output_devices():
            if device.is_virtual_device:
                return device

        return None
```

**Done when:**
- [ ] `find_speaker_device()` function added
- [ ] `find_virtual_mic_device()` function added
- [ ] Functions properly detect BlackHole and VB-Audio devices

---

### Task 2B.3: Update Audio Module Exports
**What:** Add new classes to the audio module's public API

**File to update:** `python/src/audio/__init__.py`

Replace the entire file with:

```python
"""
Audio processing module.

Handles audio capture from microphone and system audio,
as well as audio output to speakers and virtual microphone.
"""

from typing import Final

# Audio configuration constants
SAMPLE_RATE_MIC: Final[int] = 16000  # Hz
SAMPLE_RATE_SYSTEM: Final[int] = 24000  # Hz
SAMPLE_RATE_OUTPUT: Final[int] = 24000  # Hz
BIT_DEPTH: Final[int] = 16  # bits
CHANNELS: Final[int] = 1  # mono
CHUNK_SIZE: Final[int] = 1024  # frames

# Import capture classes
from .capture import (
    MicrophoneCapture,
    SystemAudioCapture,
    AudioChunk,
    CaptureState,
    AudioCaptureError,
    AudioDeviceError,
    AudioStreamError,
)

# Import playback classes
from .playback import (
    SpeakerOutput,
    VirtualMicOutput,
    PlaybackState,
    AudioPlaybackError,
    PlaybackDeviceError,
    PlaybackStreamError,
)

# Import device management
from .devices import (
    AudioDevice,
    AudioDeviceManager,
    DeviceType,
    list_audio_devices,
    find_microphone_device,
    find_loopback_device,
    find_speaker_device,
    find_virtual_mic_device,
)

__all__ = [
    # Constants
    "SAMPLE_RATE_MIC",
    "SAMPLE_RATE_SYSTEM",
    "SAMPLE_RATE_OUTPUT",
    "BIT_DEPTH",
    "CHANNELS",
    "CHUNK_SIZE",
    # Capture classes
    "MicrophoneCapture",
    "SystemAudioCapture",
    "AudioChunk",
    "CaptureState",
    "AudioCaptureError",
    "AudioDeviceError",
    "AudioStreamError",
    # Playback classes
    "SpeakerOutput",
    "VirtualMicOutput",
    "PlaybackState",
    "AudioPlaybackError",
    "PlaybackDeviceError",
    "PlaybackStreamError",
    # Device management
    "AudioDevice",
    "AudioDeviceManager",
    "DeviceType",
    "list_audio_devices",
    "find_microphone_device",
    "find_loopback_device",
    "find_speaker_device",
    "find_virtual_mic_device",
]
```

**Done when:**
- [ ] All new classes exported
- [ ] All new functions exported
- [ ] No import errors

---

### Task 2B.4: Create Playback Test Script
**What:** Create a test script demonstrating audio playback usage

**File to create:** `python/examples/test_audio_playback.py`

```python
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
```

**Test it:**
```bash
cd python
source venv/bin/activate
python examples/test_audio_playback.py
```

**Done when:**
- [ ] Script runs without errors
- [ ] Test tones play through speakers
- [ ] Device enumeration works
- [ ] Stats are displayed correctly

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
