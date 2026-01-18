# Specification - Zoom Real-Time Speech-to-Speech Translator

> Version: 1.0.0
> Created: 2026-01-18
> Status: Active

---

## Table of Contents
1. [MVP Definition](#mvp-definition)
2. [Phase 1: Project Setup](#phase-1-project-setup)
3. [Phase 2: Core Implementation](#phase-2-core-implementation)
4. [Phase 3: UI & Integration](#phase-3-ui--integration)
5. [Phase 4: Polish & Packaging](#phase-4-polish--packaging)
6. [Dependencies](#dependencies)
7. [Risk Analysis](#risk-analysis)

---

## MVP Definition

### What is the Minimum Viable Product?

The MVP is a **functional desktop application** that enables a user to have a live Zoom call with bidirectional real-time translation. The user speaks in their native language, and Zoom participants hear translated audio. When Zoom participants speak, the user hears translated audio in their language.

### MVP Success Criteria

| Criteria | Requirement |
|----------|-------------|
| Outgoing translation | User's mic input is translated and sent to Zoom via virtual mic |
| Incoming translation | Zoom audio is captured, translated, and played to user's speakers |
| Latency | < 1000ms end-to-end translation latency |
| Languages | Support at least 2 language pairs (e.g., English <-> Japanese) |
| Platform | Working on macOS (primary), Windows (secondary) |
| Stability | Can run for 30+ minutes without crash or memory leak |
| UI | Basic controls: start/stop, language selection, device selection |

### MVP Non-Goals (Deferred to Post-MVP)

- Mobile support
- Multiple simultaneous language outputs
- Transcription display
- Meeting recording/export
- Auto-language detection
- Voice cloning / voice preservation
- Multi-participant tracking

---

## Phase 1: Project Setup

**Timeline:** Week 1
**Progress:** In Progress (20%)
**Goal:** Establish development environment and project structure

### Tasks

| Task | Priority | Complexity | Status |
|------|----------|------------|--------|
| Create Electron project structure | High | S | Pending |
| Create Python backend structure | High | S | Pending |
| Set up TypeScript configuration | High | S | Pending |
| Set up Python virtual environment | High | S | Pending |
| Install Electron dependencies | High | S | Pending |
| Install Python dependencies | High | S | Pending |
| Configure ESLint + Prettier | Medium | S | Pending |
| Configure Python linting (ruff/black) | Medium | S | Pending |
| Set up Git hooks (pre-commit) | Low | S | Pending |
| Verify Gemini API access | High | S | Pending |
| Install BlackHole (macOS) | High | S | Pending |
| Create development scripts | Medium | S | Pending |

### Directory Structure to Create

```
zoom-client-s2s-translator/
├── electron/
│   ├── src/
│   │   ├── main/
│   │   │   └── index.ts
│   │   ├── renderer/
│   │   │   └── index.html
│   │   └── preload/
│   │       └── index.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── electron-builder.yml
│   └── vite.config.ts
├── python/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── audio/
│   │   │   └── __init__.py
│   │   ├── gemini/
│   │   │   └── __init__.py
│   │   └── routing/
│   │       └── __init__.py
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── tests/
│       └── __init__.py
├── scripts/
│   ├── install-blackhole.sh
│   └── dev.sh
└── .env.example
```

### Success Criteria

- [ ] `npm install` in electron/ completes without errors
- [ ] `pip install -r requirements.txt` in python/ completes without errors
- [ ] Electron app launches with blank window
- [ ] Python backend starts without errors
- [ ] Gemini API responds to test request
- [ ] BlackHole virtual audio device appears in system audio settings

### Technical Requirements

| Requirement | Version | Notes |
|-------------|---------|-------|
| Node.js | >= 20.0.0 | LTS recommended |
| npm | >= 10.0.0 | Comes with Node.js |
| Python | >= 3.10 | 3.11+ recommended |
| Electron | >= 28.0.0 | Latest stable |
| macOS | >= 13.0 | For electron-audio-loopback |
| Windows | >= 10 | For VB-Audio support |

### Environment Variables

```bash
# .env.example
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GEMINI_MODEL=gemini-2.5-flash-s2st-exp-11-2025
DEBUG=false
```

---

## Phase 2: Core Implementation

**Timeline:** Weeks 2-4
**Progress:** Not Started (0%)
**Goal:** Implement audio capture, Gemini API integration, and audio routing

### 2A: Audio Capture (Week 2)

| Task | Priority | Complexity | Status |
|------|----------|------------|--------|
| Implement MicrophoneCapture class | High | M | Pending |
| Implement SystemAudioCapture class | High | L | Pending |
| Implement audio device enumeration | High | M | Pending |
| Test microphone capture with file output | High | S | Pending |
| Test system audio capture with file output | High | M | Pending |
| Handle device hot-plug/unplug | Medium | M | Pending |

**Success Criteria:**
- [ ] Can capture mic audio and save to WAV file
- [ ] Can capture system audio and save to WAV file
- [ ] Audio format matches Gemini requirements (16-bit PCM, 16kHz/24kHz)
- [ ] Device selection UI lists available devices
- [ ] Graceful handling when device is disconnected

### 2B: Gemini API Integration (Week 3)

| Task | Priority | Complexity | Status |
|------|----------|------------|--------|
| Implement GeminiS2STClient class | High | L | Pending |
| Establish WebSocket connection | High | M | Pending |
| Implement audio streaming (send) | High | M | Pending |
| Implement audio receiving | High | M | Pending |
| Handle connection errors/reconnection | High | M | Pending |
| Implement transcription extraction | Medium | S | Pending |
| Test single-direction translation | High | M | Pending |

**Success Criteria:**
- [ ] WebSocket connection established to Gemini API
- [ ] Audio can be streamed to API
- [ ] Translated audio received from API
- [ ] End-to-end latency measured and documented
- [ ] Automatic reconnection on connection drop

### 2C: Audio Routing (Week 4)

| Task | Priority | Complexity | Status |
|------|----------|------------|--------|
| Implement SpeakerOutput class | High | M | Pending |
| Implement VirtualMicOutput class | High | L | Pending |
| Implement IncomingPipeline | High | L | Pending |
| Implement OutgoingPipeline | High | L | Pending |
| Buffer management for smooth playback | High | M | Pending |
| Test full bidirectional flow | High | L | Pending |

**Success Criteria:**
- [ ] Translated audio plays through speakers correctly
- [ ] Translated audio routes to virtual mic (BlackHole)
- [ ] Zoom receives audio from virtual mic
- [ ] No audio feedback loops
- [ ] Audio quality acceptable (no crackling/dropouts)

### Technical Specifications

**Audio Formats:**
| Stream | Sample Rate | Bit Depth | Channels |
|--------|-------------|-----------|----------|
| Mic Input | 16kHz | 16-bit | Mono |
| System Capture | 24kHz | 16-bit | Mono/Stereo |
| API Output | 24kHz | 16-bit | Mono |
| Virtual Mic | 24kHz | 16-bit | Mono |

**Gemini API Configuration:**
```python
config = LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=SpeechConfig(language_code="TARGET_LANG"),
    enable_speech_to_speech_translation=True
)
```

---

## Phase 3: UI & Integration

**Timeline:** Week 5
**Progress:** Not Started (0%)
**Goal:** Build Electron UI and integrate with Python backend

### Tasks

| Task | Priority | Complexity | Status |
|------|----------|------------|--------|
| Design UI mockups | Medium | S | Pending |
| Implement main window layout | High | M | Pending |
| Implement LanguageSelector component | High | M | Pending |
| Implement DeviceSelector component | High | M | Pending |
| Implement StatusPanel component | High | M | Pending |
| Implement start/stop controls | High | M | Pending |
| Implement Python subprocess manager | High | L | Pending |
| Implement IPC protocol (Electron <-> Python) | High | L | Pending |
| Settings persistence (electron-store) | Medium | M | Pending |
| System tray integration | Medium | M | Pending |
| Keyboard shortcuts | Low | S | Pending |

**Success Criteria:**
- [ ] UI displays current translation status
- [ ] User can select source and target languages
- [ ] User can select audio devices
- [ ] Start/Stop button controls translation
- [ ] Settings persist between sessions
- [ ] App minimizes to system tray
- [ ] Global keyboard shortcut to toggle translation

### UI Components

**Main Window:**
```
+------------------------------------------+
|  Zoom S2S Translator              _ [] X |
+------------------------------------------+
|                                          |
|  Source Language: [English     v]        |
|  Target Language: [Japanese    v]        |
|                                          |
|  Microphone:      [Built-in Mic   v]     |
|  Speaker:         [Headphones     v]     |
|                                          |
|  Status: [Idle / Translating...]         |
|  Latency: [-- ms]                        |
|                                          |
|  [    START TRANSLATION    ]             |
|                                          |
+------------------------------------------+
```

### IPC Message Types

| Type | Direction | Payload |
|------|-----------|---------|
| start | Electron -> Python | { sourceLang, targetLang, micDevice, speakerDevice } |
| stop | Electron -> Python | {} |
| status | Python -> Electron | { incoming, outgoing, latency } |
| error | Python -> Electron | { code, message } |
| devices | Electron -> Python | {} |
| devices_response | Python -> Electron | { microphones: [], speakers: [] } |

---

## Phase 4: Polish & Packaging

**Timeline:** Weeks 6-7
**Progress:** Not Started (0%)
**Goal:** Error handling, testing, and distribution packaging

### 4A: Error Handling & Stability (Week 6)

| Task | Priority | Complexity | Status |
|------|----------|------------|--------|
| Comprehensive error handling in audio pipeline | High | M | Pending |
| Gemini API error handling & retry logic | High | M | Pending |
| Device disconnection handling | High | M | Pending |
| Memory leak testing & fixes | High | M | Pending |
| Logging system implementation | High | M | Pending |
| Unit tests for Python modules | Medium | L | Pending |
| Integration tests | Medium | L | Pending |
| 30-minute stability test | High | M | Pending |

**Success Criteria:**
- [ ] No unhandled exceptions crash the app
- [ ] Graceful degradation when devices unavailable
- [ ] Memory usage stable over 1-hour session
- [ ] Logs written to file for debugging
- [ ] 80%+ test coverage on critical paths

### 4B: Packaging & Distribution (Week 7)

| Task | Priority | Complexity | Status |
|------|----------|------------|--------|
| Configure electron-builder for macOS | High | M | Pending |
| Configure electron-builder for Windows | High | M | Pending |
| Bundle Python runtime with app | High | L | Pending |
| Code signing (macOS) | Medium | M | Pending |
| Code signing (Windows) | Medium | M | Pending |
| Create installer scripts | High | M | Pending |
| Auto-updater implementation | Low | M | Pending |
| Create user documentation | Medium | M | Pending |
| Create setup guide for virtual audio | High | M | Pending |

**Success Criteria:**
- [ ] DMG installer works on fresh macOS system
- [ ] EXE installer works on fresh Windows system
- [ ] Python runtime bundled (no user installation required)
- [ ] Virtual audio setup guide included
- [ ] App passes macOS notarization
- [ ] App passes Windows SmartScreen

### Packaging Configuration

**electron-builder.yml:**
```yaml
appId: com.zoom-translator.app
productName: Zoom S2S Translator
directories:
  output: dist
mac:
  category: public.app-category.productivity
  target:
    - dmg
    - zip
  hardenedRuntime: true
  notarize: true
win:
  target:
    - nsis
    - portable
extraResources:
  - from: python-dist/
    to: python/
```

---

## Dependencies

### Electron (package.json)

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

### Python (requirements.txt)

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
asyncio>=3.4.3

# Utilities
python-dotenv>=1.0.0
pydantic>=2.5.0

# Development
pytest>=7.4.0
pytest-asyncio>=0.21.0
ruff>=0.1.0
black>=23.0.0
```

### System Dependencies

| Dependency | Platform | Purpose | Installation |
|------------|----------|---------|--------------|
| BlackHole | macOS | Virtual audio routing | brew install blackhole-2ch |
| VB-Audio Virtual Cable | Windows | Virtual audio routing | Manual installer |
| PortAudio | macOS/Windows | PyAudio dependency | brew install portaudio / pip install |
| Xcode CLI Tools | macOS | Build tools | xcode-select --install |

---

## Risk Analysis

### Technical Risks

| Risk | Probability | Impact | Severity | Mitigation |
|------|-------------|--------|----------|------------|
| Gemini S2ST API exits preview/becomes paid | Medium | High | High | Implement fallback STT+Translate+TTS pipeline |
| Audio latency exceeds 1000ms | Medium | High | High | Optimize chunk sizes, test different buffer configs |
| Virtual audio driver issues | Low | Medium | Medium | Support multiple drivers, provide troubleshooting guide |
| Electron + Python IPC instability | Low | High | Medium | Use well-tested IPC patterns, implement heartbeat |
| Memory leaks in audio streaming | Medium | Medium | Medium | Profile regularly, use async generators properly |
| macOS audio permissions | Low | High | Medium | Clear permission prompts, documentation |
| Windows audio exclusivity mode | Low | Medium | Low | Use shared mode audio, document limitations |

### Business/Operational Risks

| Risk | Probability | Impact | Severity | Mitigation |
|------|-------------|--------|----------|------------|
| Zoom changes audio routing | Low | High | Medium | Monitor Zoom updates, maintain compatibility layer |
| User setup complexity too high | Medium | Medium | Medium | Provide detailed guides, consider auto-setup scripts |
| Competitor releases similar product | Medium | Medium | Low | Focus on quality and developer velocity |

### Risk Monitoring

- **Weekly:** Check Gemini API status and documentation for changes
- **Per Release:** Test on fresh OS installations
- **Continuous:** Monitor GitHub issues for audio driver problems

---

## Appendix

### Language Support

The Gemini S2ST API supports 100+ languages. Priority languages for MVP:

| Language | Code | Priority |
|----------|------|----------|
| English | en | MVP |
| Japanese | ja | MVP |
| Spanish | es | High |
| French | fr | High |
| German | de | High |
| Mandarin Chinese | cmn | High |
| Korean | ko | Medium |
| Hindi | hi | Medium |
| Arabic | ar | Medium |
| Portuguese | pt | Medium |

### Performance Benchmarks

| Metric | Target | Minimum | Notes |
|--------|--------|---------|-------|
| Translation Latency | < 500ms | < 1000ms | End-to-end |
| Audio Quality | 24kHz | 16kHz | Output sample rate |
| Memory (Idle) | < 200MB | < 500MB | Combined Electron + Python |
| Memory (Active) | < 500MB | < 1GB | During translation |
| CPU (Idle) | < 5% | < 10% | Background usage |
| CPU (Active) | < 30% | < 50% | During translation |
| Startup Time | < 3s | < 5s | App launch to ready |

### Testing Checklist

**Before Each Release:**
- [ ] 30-minute continuous translation test
- [ ] Test on fresh macOS installation
- [ ] Test on fresh Windows installation
- [ ] Verify all language pairs work
- [ ] Memory usage stays stable
- [ ] No audio quality degradation over time
- [ ] Virtual audio routing verified with Zoom

---

*This specification is a living document. Update as requirements evolve.*
