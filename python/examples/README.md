# Audio Capture Examples

Example scripts demonstrating usage of the audio capture components.

## Prerequisites

1. Install Python dependencies:
   ```bash
   cd python
   pip install -r requirements.txt
   ```

2. For system audio capture, install a virtual audio device:
   - **macOS**: Install [BlackHole](https://github.com/ExistentialAudio/BlackHole)
     ```bash
     brew install blackhole-2ch
     ```
   - **Windows**: Install [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)

## Available Examples

### test_audio_capture.py

Demonstrates microphone and system audio capture.

**Features:**
- Enumerate and list all audio devices
- Capture audio from microphone
- Capture system audio (with virtual device)
- Display capture statistics

**Usage:**
```bash
cd python
python examples/test_audio_capture.py
```

**What it does:**
1. Lists all available audio devices
2. Captures 5 seconds of microphone audio
3. Displays statistics (chunks, bytes, timing)

**Expected output:**
```
=== Testing Device Enumeration ===
Found 8 total devices
Physical input devices: 2
  [0] Built-in Microphone (in: 2, out: 0, 44100Hz) [default input]
  [1] External USB Mic (in: 1, out: 0, 48000Hz)

Virtual/Loopback devices: 1
  [5] BlackHole 2ch (in: 2, out: 2, 48000Hz) [virtual]

=== Testing Microphone Capture ===
Using device: [0] Built-in Microphone
Capturing audio for 5 seconds...
Speak into your microphone!
Received 10 chunks, 20480 bytes, 64.0ms per chunk
Received 20 chunks, 40960 bytes, 64.0ms per chunk
...
Final stats: {'chunks_captured': 78, 'bytes_captured': 159744, 'overruns': 0, 'queue_size': 0}
Captured 78 chunks, 156.0 KB in 5s
```

## Testing Individual Components

### Test Device Enumeration Only

```python
import asyncio
from audio import AudioDeviceManager

async def main():
    with AudioDeviceManager() as manager:
        manager.print_all_devices()

        # Find specific devices
        default_mic = manager.get_default_input_device()
        print(f"\nDefault microphone: {default_mic}")

        blackhole = manager.find_blackhole_device()
        if blackhole:
            print(f"BlackHole device: {blackhole}")

asyncio.run(main())
```

### Test Microphone Capture Only

```python
import asyncio
from audio import MicrophoneCapture

async def main():
    async with MicrophoneCapture() as mic:
        print(f"Capturing at {mic.sample_rate}Hz...")

        for i in range(10):
            chunk = await mic.read_chunk()
            print(f"Chunk {i}: {len(chunk.data)} bytes")

        print(f"Stats: {mic.stats}")

asyncio.run(main())
```

### Test System Audio Capture

```python
import asyncio
from audio import SystemAudioCapture, find_loopback_device

async def main():
    loopback = find_loopback_device()
    if not loopback:
        print("No virtual audio device found!")
        return

    print(f"Using: {loopback}")

    async with SystemAudioCapture(device_index=loopback.index) as system:
        print("Capturing system audio for 5 seconds...")
        print("Play some audio!")

        for i in range(80):  # ~5 seconds at 16 chunks/sec
            chunk = await system.read_chunk(timeout=1.0)
            if i % 10 == 0:
                print(f"Chunk {i}: {len(chunk.data)} bytes")

        print(f"Stats: {system.stats}")

asyncio.run(main())
```

## Troubleshooting

### No audio devices found
- Check that PyAudio is installed correctly
- On macOS, ensure you've granted microphone permissions
- On Linux, check ALSA/PulseAudio configuration

### "No virtual audio device found"
- Install BlackHole (macOS) or VB-Audio Cable (Windows)
- Verify device appears in system audio settings
- Restart the script after installation

### Audio buffer overruns
- Reduce CPU load on your system
- Close other audio applications
- Try increasing queue size in capture classes

### Permission denied errors
- macOS: Grant Terminal microphone access in System Preferences → Security & Privacy
- Windows: Check Windows privacy settings for microphone access
- Linux: Ensure user is in 'audio' group

## Next Steps

After verifying audio capture works:
1. Implement audio playback (Phase 2B)
2. Integrate with Gemini S2ST API (Phase 3)
3. Build complete translation pipeline
