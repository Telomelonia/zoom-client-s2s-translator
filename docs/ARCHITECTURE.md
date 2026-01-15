# Architecture - Zoom S2S Translator

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ZOOM APPLICATION                                │
│   ┌─────────────┐                                    ┌─────────────────┐    │
│   │ Zoom Audio  │◄───────────────────────────────────│ Zoom Mic Input  │    │
│   │   Output    │                                    │ (Virtual Mic)   │    │
│   └──────┬──────┘                                    └────────▲────────┘    │
└──────────┼───────────────────────────────────────────────────┼──────────────┘
           │                                                    │
           ▼                                                    │
┌──────────────────────────────────────────────────────────────────────────────┐
│                        ZOOM S2S TRANSLATOR APP                               │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         ELECTRON SHELL                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │ │
│  │  │    Main      │  │   Renderer   │  │   Preload    │  │  System    │ │ │
│  │  │   Process    │◄─┤    (UI)      │  │   Bridge     │  │   Tray     │ │ │
│  │  └──────┬───────┘  └──────────────┘  └──────────────┘  └────────────┘ │ │
│  │         │ IPC                                                          │ │
│  └─────────┼──────────────────────────────────────────────────────────────┘ │
│            │                                                                 │
│            ▼                                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         PYTHON BACKEND                                  │ │
│  │                                                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │                    INCOMING TRANSLATION FLOW                     │  │ │
│  │  │                    (Zoom participants → You)                     │  │ │
│  │  │                                                                  │  │ │
│  │  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │  │ │
│  │  │  │ System Audio │    │  Gemini S2ST │    │   Speaker    │       │  │ │
│  │  │  │   Capture    │───▶│  WebSocket   │───▶│   Output     │       │  │ │
│  │  │  │  (loopback)  │    │  (Translate) │    │  (PyAudio)   │       │  │ │
│  │  │  └──────────────┘    └──────────────┘    └──────────────┘       │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │                    OUTGOING TRANSLATION FLOW                     │  │ │
│  │  │                    (You → Zoom participants)                     │  │ │
│  │  │                                                                  │  │ │
│  │  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │  │ │
│  │  │  │  Microphone  │    │  Gemini S2ST │    │  Virtual Mic │───────┼──┼─┘
│  │  │  │    Input     │───▶│  WebSocket   │───▶│   Output     │       │  │
│  │  │  │  (PyAudio)   │    │  (Translate) │    │ (BlackHole)  │       │  │
│  │  │  └──────────────┘    └──────────────┘    └──────────────┘       │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Electron Shell

#### Main Process (`electron/src/main/`)
```typescript
// Responsibilities:
- Spawn and manage Python backend subprocess
- IPC communication with renderer
- System tray integration
- Window management
- Auto-updater integration
```

#### Renderer Process (`electron/src/renderer/`)
```typescript
// Responsibilities:
- User interface (React/Vue/Svelte)
- Settings management
- Language selection
- Audio device selection
- Status display
- Transcription display (optional)
```

#### Preload Bridge (`electron/src/preload/`)
```typescript
// Responsibilities:
- Secure IPC bridge between main and renderer
- Expose limited API to renderer
```

### 2. Python Backend

#### Audio Module (`python/src/audio/`)
```python
# capture.py - Audio input handling
class MicrophoneCapture:
    """Captures audio from physical microphone"""
    - PyAudio stream (16kHz, 16-bit PCM, mono)
    - Async queue for audio chunks
    - Device selection support

class SystemAudioCapture:
    """Captures system audio (Zoom output)"""
    - Uses loopback device
    - macOS: BlackHole or electron-audio-loopback
    - Windows: VB-Audio Virtual Cable

# playback.py - Audio output handling
class SpeakerOutput:
    """Plays translated audio to speakers"""
    - PyAudio output stream (24kHz)
    - Buffer management for smooth playback

class VirtualMicOutput:
    """Routes translated audio to virtual microphone"""
    - Writes to BlackHole/VB-Audio input
    - This becomes Zoom's microphone input
```

#### Gemini Module (`python/src/gemini/`)
```python
# client.py - Vertex AI S2ST integration
class GeminiS2STClient:
    """WebSocket client for Gemini S2ST API"""

    async def connect(self, source_lang: str, target_lang: str):
        """Establish WebSocket connection with translation config"""
        config = LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=SpeechConfig(language_code=target_lang),
            enable_speech_to_speech_translation=True
        )

    async def send_audio(self, audio_chunk: bytes):
        """Stream audio chunk to Gemini"""

    async def receive_audio(self) -> bytes:
        """Receive translated audio from Gemini"""

    async def get_transcription(self) -> tuple[str, str]:
        """Get input and output transcriptions"""
```

#### Routing Module (`python/src/routing/`)
```python
# pipeline.py - Main translation pipelines
class IncomingPipeline:
    """Zoom audio → Translation → Your speakers"""
    - Captures system audio (Zoom output)
    - Sends to Gemini S2ST
    - Plays translated audio to speakers

class OutgoingPipeline:
    """Your voice → Translation → Zoom"""
    - Captures microphone input
    - Sends to Gemini S2ST
    - Routes translated audio to virtual mic
```

---

## Data Flow

### Incoming Translation (Zoom → You)
```
1. Zoom outputs audio through system speakers
2. System audio capture (loopback) intercepts audio
3. Audio streamed to Gemini S2ST WebSocket
4. Gemini returns translated audio
5. Translated audio played through your headphones/speakers
```

### Outgoing Translation (You → Zoom)
```
1. You speak into your physical microphone
2. PyAudio captures microphone input
3. Audio streamed to Gemini S2ST WebSocket
4. Gemini returns translated audio
5. Translated audio routed to virtual microphone (BlackHole)
6. Zoom receives audio from virtual microphone
```

---

## Audio Device Configuration

### macOS Setup
```
Physical Devices:
- Input: Built-in Microphone / External Mic
- Output: Built-in Speakers / Headphones

Virtual Devices (BlackHole):
- BlackHole 2ch: Virtual microphone for Zoom

App Configuration:
- Mic Input: Physical microphone
- System Capture: Multi-Output Device (includes BlackHole)
- Speaker Output: Physical speakers/headphones
- Virtual Mic Out: BlackHole 2ch

Zoom Configuration:
- Microphone: BlackHole 2ch
- Speaker: Multi-Output Device
```

### Windows Setup
```
Physical Devices:
- Input: Default Microphone
- Output: Default Speakers

Virtual Devices (VB-Audio):
- CABLE Input: Virtual microphone for Zoom
- CABLE Output: Loopback for system capture

App Configuration:
- Mic Input: Physical microphone
- System Capture: CABLE Output (loopback)
- Speaker Output: Physical speakers
- Virtual Mic Out: CABLE Input

Zoom Configuration:
- Microphone: CABLE Input (VB-Audio)
- Speaker: Default speakers
```

---

## IPC Protocol

### Electron ↔ Python Communication

```typescript
// Message types
interface IPCMessage {
  type: 'start' | 'stop' | 'config' | 'status' | 'error';
  payload: any;
}

// Start translation
{ type: 'start', payload: {
    sourceLang: 'en',
    targetLang: 'ja',
    micDevice: 'device-id',
    speakerDevice: 'device-id'
}}

// Stop translation
{ type: 'stop', payload: {} }

// Status update (Python → Electron)
{ type: 'status', payload: {
    incoming: 'active' | 'idle',
    outgoing: 'active' | 'idle',
    latency: 250,  // ms
    inputTranscript: 'Hello',
    outputTranscript: 'こんにちは'
}}

// Error
{ type: 'error', payload: {
    code: 'AUDIO_DEVICE_ERROR',
    message: 'Microphone not found'
}}
```

---

## File Structure

```
zoom-client-s2s-translator/
├── electron/
│   ├── src/
│   │   ├── main/
│   │   │   ├── index.ts          # Main entry point
│   │   │   ├── python-bridge.ts  # Python subprocess manager
│   │   │   ├── tray.ts           # System tray
│   │   │   └── updater.ts        # Auto-updater
│   │   ├── renderer/
│   │   │   ├── App.tsx           # Main UI component
│   │   │   ├── components/
│   │   │   │   ├── LanguageSelector.tsx
│   │   │   │   ├── DeviceSelector.tsx
│   │   │   │   ├── StatusPanel.tsx
│   │   │   │   └── TranscriptView.tsx
│   │   │   └── stores/
│   │   │       └── settings.ts
│   │   └── preload/
│   │       └── index.ts          # IPC bridge
│   ├── package.json
│   ├── tsconfig.json
│   ├── electron-builder.yml
│   └── vite.config.ts
│
├── python/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py               # Entry point
│   │   ├── audio/
│   │   │   ├── __init__.py
│   │   │   ├── capture.py        # Mic & system audio capture
│   │   │   ├── playback.py       # Speaker & virtual mic output
│   │   │   └── devices.py        # Device enumeration
│   │   ├── gemini/
│   │   │   ├── __init__.py
│   │   │   ├── client.py         # S2ST WebSocket client
│   │   │   └── config.py         # API configuration
│   │   ├── routing/
│   │   │   ├── __init__.py
│   │   │   └── pipeline.py       # Translation pipelines
│   │   └── ipc/
│   │       ├── __init__.py
│   │       └── handler.py        # Electron IPC handler
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── tests/
│       └── ...
│
├── docs/
│   ├── PROJECT_STATUS.md
│   ├── ARCHITECTURE.md
│   └── SETUP_GUIDE.md
│
├── scripts/
│   ├── install-blackhole.sh      # macOS virtual audio setup
│   └── install-vbaudio.ps1       # Windows virtual audio setup
│
├── CLAUDE.md
├── README.md
├── .gitignore
└── LICENSE
```

---

## Dependencies

### Electron (package.json)
```json
{
  "dependencies": {
    "electron-audio-loopback": "^1.0.0"
  },
  "devDependencies": {
    "electron": "^28.0.0",
    "electron-builder": "^24.0.0",
    "vite": "^5.0.0",
    "typescript": "^5.3.0",
    "@types/node": "^20.0.0"
  }
}
```

### Python (requirements.txt)
```
google-cloud-aiplatform>=1.38.0
pyaudio>=0.2.14
websockets>=12.0
numpy>=1.26.0
sounddevice>=0.4.6
python-dotenv>=1.0.0
```

---

## Security Considerations

1. **API Authentication**
   - Use service account for backend (secure)
   - Never expose API keys in frontend
   - Use ephemeral tokens for any client-side calls

2. **Audio Privacy**
   - All audio processed locally before API call
   - No audio stored permanently
   - Clear user consent for audio capture

3. **IPC Security**
   - Validate all messages between Electron and Python
   - Sanitize any file paths or commands
   - Use contextIsolation in Electron

---

## Performance Targets

| Metric | Target | Acceptable |
|--------|--------|------------|
| Translation latency | <500ms | <1000ms |
| Audio quality | 24kHz | 16kHz |
| Memory usage | <500MB | <1GB |
| CPU usage (idle) | <5% | <10% |
| CPU usage (active) | <30% | <50% |
