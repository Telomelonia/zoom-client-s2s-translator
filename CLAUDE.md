# CLAUDE.md - Project Intelligence

## AGENT ROUTING - READ FIRST

### Default Behavior
When the user makes ANY request:
1. **ALWAYS invoke @project-manager first**
2. Project Manager coordinates with other agents as needed
3. NEVER skip directly to senior-developer or junior-developer

### User Bypass Commands (explicit only)
- `/senior [request]` - Direct senior developer access
- `/junior [request]` - Direct junior developer access

### Orchestration Overview
```
User → Project Manager → Senior Developer → Junior Developer
                ↑                                    │
                └────────────────────────────────────┘
```

See `docs/ORCHESTRATION_PROTOCOL.md` for full details.

---

## Project Overview
**Name:** Zoom Real-Time Speech-to-Speech Translator
**Goal:** Mac/Windows desktop app providing live bidirectional translation for Zoom calls using Google's Gemini Live API (S2ST)

## Tech Stack Decision
- **Frontend:** Electron (TypeScript)
- **Backend:** Python (FastAPI or direct IPC)
- **Translation API:** Vertex AI Gemini Live API - Speech-to-Speech Translation
- **Model:** Set via `GEMINI_MODEL` env var (see `.env.example`)
- **Audio:** PyAudio (input), electron-audio-loopback (system capture)
- **Virtual Audio:** BlackHole (macOS), VB-Audio Virtual Cable (Windows)
- **Packaging:** electron-builder (DMG + EXE)

## API Configuration
```python
# Gemini S2ST Configuration
speech_config = SpeechConfig(language_code="TARGET_LANG")
config = LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=speech_config,
    enable_speech_to_speech_translation=True
)
```

## Audio Specifications
- **Input format:** 16-bit PCM, 16kHz, mono (mic) / 24kHz (system)
- **Output format:** 24kHz PCM
- **Chunk size:** 1024 frames
- **Supported languages:** 100+ (including cmn, ja, es, fr, de, hi, ar, etc.)

## Architecture Flow
```
YOUR MIC → PyAudio → Gemini S2ST → Translated Audio → Virtual Mic → Zoom
ZOOM AUDIO → System Capture → Gemini S2ST → Translated Audio → Your Speakers
```

## Key Files Structure (Target)
```
zoom-client-s2s-translator/
├── electron/                 # Electron frontend
│   ├── src/
│   │   ├── main/            # Main process
│   │   ├── renderer/        # UI components
│   │   └── preload/         # IPC bridge
│   ├── package.json
│   └── electron-builder.yml
├── python/                   # Python backend
│   ├── src/
│   │   ├── audio/           # Audio capture/playback
│   │   ├── gemini/          # Vertex AI integration
│   │   └── routing/         # Virtual audio routing
│   ├── requirements.txt
│   └── main.py
├── docs/
│   ├── PROJECT_STATUS.md    # Progress tracking
│   └── ARCHITECTURE.md      # Technical design
├── CLAUDE.md                # This file
└── README.md
```

## Manager Agent Rules

### Progress Tracking
- Always update `docs/PROJECT_STATUS.md` after completing tasks
- Track blockers, decisions, and milestones
- Maintain task completion percentage

### Research Protocol
- When uncertain, research using WebSearch/WebFetch first
- Verify API availability and documentation accuracy
- Document findings in relevant .md files

### Code Standards
- Python: Use type hints, async/await for audio streams
- TypeScript: Strict mode, proper IPC typing
- Error handling: Graceful degradation for audio failures
- Security: Use ephemeral tokens for Gemini API (client-side)

### Decision Log
All major decisions must be logged in PROJECT_STATUS.md with:
- Date
- Decision made
- Rationale
- Alternatives considered

## Current Status
**Phase:** Gemini Integration (Phase 3) - 80% complete
**Last Completed:** Bidirectional translation CLI (`translate.py`) with upstream/downstream modes
**Progress:** 65%
**API Status:** Gemini S2ST available (Private Preview, FREE) - connection verified
**Blockers:** BlackHole not visible in PyAudio (needs Mac reboot for kernel driver)

## Commands for Manager Agent
When user says:
- `/status` → Read and summarize PROJECT_STATUS.md
- `/update [message]` → Add progress update to PROJECT_STATUS.md
- `/research [topic]` → Research and document findings
- `/decide [options]` → Analyze options and recommend decision
- `/plan [feature]` → Break down feature into tasks

## Important Links
- Gemini Live API: https://ai.google.dev/gemini-api/docs/live
- S2ST Documentation: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/live-api/speech-to-speech-translation
- BlackHole Audio: https://github.com/ExistentialAudio/BlackHole
- electron-audio-loopback: https://github.com/alectrocute/electron-audio-loopback
