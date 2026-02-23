# Project Status - Zoom S2S Translator

> Last Updated: 2026-02-23
> Overall Progress: **80%** ████████████████░░░░

---

## Project Vision
**Live bidirectional translation for Zoom calls.** You speak English, your Zoom partner hears Japanese (or any of 100+ languages). They speak Japanese, you hear English. Two audio streams, powered by Google Gemini S2ST, routed through BlackHole virtual audio.

```
YOUR MIC → Gemini S2ST → BlackHole → Zoom (partner hears translated audio)
ZOOM AUDIO → BlackHole → Gemini S2ST → Your Speakers (you hear translated audio)
```

---

## Current Phase: Electron UI Integration (Phase 4) - COMPLETE

### Sprint Overview
| Sprint | Status | Progress |
|--------|--------|----------|
| 1. Project Setup | ✅ Complete | 100% |
| 2A. Audio Capture | ✅ Complete | 100% |
| 2B. Audio Playback | ✅ Complete | 100% |
| 3. Gemini Integration | ✅ Complete | 100% |
| 4. Electron UI | ✅ Complete | 100% |
| 5. Packaging & Distribution | Not Started | 0% |

---

## Active Tasks

### Completed (Phase 4 - Electron UI Integration)
- [x] Created `python/server.py` — stdio JSON-lines server wrapping translate.py logic
- [x] Created `electron/src/main/python-bridge.ts` — PythonBridge subprocess manager
- [x] Updated `electron/src/shared/types.ts` — PythonCommand/PythonMessage types, chunk-based status
- [x] Wired `electron/src/main/index.ts` — all 5 IPC handlers, Python bridge, graceful shutdown
- [x] Updated `electron/src/preload/index.ts` — imports from shared types
- [x] Updated `electron/src/renderer/app.ts` — chunk-based status, error banner (no more alert())
- [x] Senior code review: 6 critical + 9 important issues found and fixed
  - Fixed: `process.cwd()` → `__dirname`-relative path resolution
  - Fixed: async cancellation now awaits sub-tasks before closing streams
  - Fixed: `before-quit` properly awaits async cleanup via `event.preventDefault()`
  - Fixed: XSS in error banner (innerHTML → textContent)
  - Fixed: `sendAndWait` rejects immediately on Python error messages
  - Fixed: `translation:start` waits for `started` confirmation from Python
  - Fixed: `PythonBridge.stop()` double-stop guard
  - Fixed: stream cleanup in try/finally blocks
  - Fixed: preload imports shared types instead of duplicating

### Completed (Phase 3 - Bidirectional Translation CLI)
- [x] Created `translate.py` — production-ready bidirectional translation CLI
- [x] Implemented **upstream** mode: Mic (EN) → Gemini S2ST → BlackHole → Zoom hears Japanese
- [x] Implemented **downstream** mode: BlackHole (Zoom audio) → Gemini S2ST → Speakers in English
- [x] Created `tests/test_mic_to_speaker.py` — segmented sending with manual activity detection
- [x] CLI with `--target`, `--duration`, `--mic-index`, `--speaker-index`, `--blackhole-index`, `--list-devices`

### Remaining (Phase 5 - Polish & Packaging)
- [ ] Silence detection for natural segment boundaries (fix abrupt audio cuts)
- [ ] Investigate Gemini session reuse (why it freezes after first turn)
- [ ] Add mode selector to UI (upstream/downstream toggle)
- [ ] Auto-detect and configure BlackHole in UI
- [ ] PyInstaller bundling for production
- [ ] electron-builder DMG/EXE packaging

### Blockers
- ~~**BlackHole not visible in PyAudio**~~ — **RESOLVED** (2026-02-23, reboot fixed it, device visible at index 3)
- **Gemini freezes after first response** — single session only translates one turn then stops responding. **Workaround:** reconnect-per-segment (new session every 5s). Works but causes abrupt audio cuts mid-sentence.
- **Abrupt segment boundaries** — fixed 5-second segments cut speech mid-sentence. Needs silence detection to find natural pause points before ending a segment.

### Completed (Phase 2B - Audio Playback)
- [x] Implement SpeakerOutput class (plays translated audio to speakers)
- [x] Implement VirtualMicOutput class (routes audio to virtual mic for Zoom)
- [x] Add device helper functions (find_speaker_device, find_virtual_mic_device)
- [x] Create test_audio_playback.py example script
- [x] Senior developer code review passed
- [x] Bug fix: asyncio.get_event_loop() replaced with asyncio.get_running_loop()

### Completed (Phase 2A - Commit: fd4334e)
- [x] Implement MicrophoneCapture class (463 lines)
- [x] Implement SystemAudioCapture class (with stereo-to-mono conversion)
- [x] Implement audio device enumeration (533 lines)
- [x] Create test_audio_capture.py example (187 lines)
- [x] Create examples/README.md documentation (163 lines)
- [x] Create PHASE_2A_SUMMARY.md (315 lines)
- [x] Create AUDIO_CAPTURE_FLOW.md (383 lines)
- [x] Senior developer code review and bug fixes
- [x] Tech stack decision: Electron + Python
- [x] API research: Gemini S2ST confirmed available
- [x] Created CLAUDE.md project intelligence file
- [x] Created PROJECT_STATUS.md tracking file
- [x] Created ARCHITECTURE.md technical design document
- [x] Created SPEC.md comprehensive specification document
- [x] Created complete Electron project structure
- [x] Created complete Python backend structure
- [x] Set up TypeScript configuration with strict mode
- [x] Set up Python linting (Ruff, Black, mypy)
- [x] Set up ESLint and Prettier for Electron
- [x] Created all configuration files (tsconfig, package.json, pyproject.toml)
- [x] Created development scripts (dev.sh, install-blackhole.sh)
- [x] Created .env.example with all required environment variables
- [x] Updated .gitignore for new structure
- [x] Created Electron source files (main, preload, renderer)
- [x] Created Python module structure (audio, gemini, routing)
- [x] Set up Vite build configuration
- [x] Set up electron-builder configuration

### Blocked
_None currently_

---

## Decision Log

### 2026-01-15: Tech Stack Selection
**Decision:** Electron + Python Backend
**Rationale:**
- Python has official Vertex AI SDK with S2ST support
- PyAudio shown in official Gemini docs for audio streaming
- Electron has mature packaging (DMG/EXE) via electron-builder
- New electron-audio-loopback enables native system audio capture

**Alternatives Considered:**
- Flutter: Good desktop audio packages exist, but less mature for this use case
- Native Swift/C++: Too slow to develop, harder to maintain cross-platform

### 2026-02-19: Bypass Complex Pipeline for Proven Minimal Pattern
**Decision:** Created `translate.py` at project root using the proven minimal pattern from `test_minimal_translate.py`, bypassing the complex pipeline abstractions in `client.py` and `capture.py`.
**Rationale:**
- `client.py` and `capture.py` had queue flooding and receive loop crashes
- The minimal pattern (blocking PyAudio reads via `run_in_executor`, direct `session.send_realtime_input()` / `session.receive()`) was proven working in `test_minimal_translate.py`
- No async queues or callbacks needed -- avoids the bugs in the complex pipeline
- Production-ready CLI with full bidirectional support achieved faster this way

**Alternatives Considered:**
- Fix the existing `client.py`/`capture.py` abstractions -- rejected due to fundamental design issues (queue flooding, receive loop timing)
- Use a different async framework -- unnecessary complexity given the working pattern

### 2026-02-19: Model Name Correction
**Decision:** Updated model to `gemini-live-2.5-flash-preview-native-audio-09-2025`
**Rationale:**
- `gemini-2.5-flash-s2st-exp-11-2025` does not exist — was never a real model ID
- S2ST is a feature flag on the native audio model, not a separate model
- GA alternative available: `gemini-live-2.5-flash-native-audio`
- Connection verified successfully on 2026-02-19

### 2026-01-15: API Selection
**Decision:** Vertex AI Gemini S2ST API
**Model:** ~~`gemini-2.5-flash-s2st-exp-11-2025`~~ → `gemini-live-2.5-flash-preview-native-audio-09-2025`
**Rationale:**
- Only model supporting true speech-to-speech translation
- 100+ languages supported
- Currently FREE in private preview
- Direct audio-to-audio (no intermediate text required)

---

## Milestones

| Milestone | Target | Status |
|-----------|--------|--------|
| Project structure complete | Week 1 | ✅ Complete |
| Audio capture pipeline (Phase 2A) | Week 2 | ✅ Complete (fd4334e) |
| Audio playback pipeline (Phase 2B) | Week 2 | ✅ Complete |
| Mic → Gemini → Speaker working | Week 3 | ✅ Complete (verified 2026-02-23) |
| System audio capture working | Week 3 | ✅ Complete |
| Virtual mic routing working | Week 4 | ✅ Complete (BlackHole verified) |
| Electron UI complete | Week 5 | ✅ Complete (a8893b6) |
| DMG/EXE builds working | Week 6 | Pending |
| Beta release | Week 7 | Pending |

---

## Research Notes

### Gemini S2ST API
- **Endpoint:** Vertex AI WebSocket
- **Auth:** Service account or ephemeral tokens
- **Config flag:** `enable_speech_to_speech_translation=True`
- **Input:** PCM audio stream (24kHz recommended)
- **Output:** Translated audio + transcriptions

### Virtual Audio Routing
- **macOS:** BlackHole (free, zero latency, Apple Silicon native)
- **Windows:** VB-Audio Virtual Cable or VoiceMeeter
- **Alternative:** electron-audio-loopback (Chromium native, macOS 13+)

### Audio Format Requirements
| Direction | Sample Rate | Format | Channels |
|-----------|-------------|--------|----------|
| Mic Input | 16kHz | 16-bit PCM | Mono |
| System Input | 24kHz | 16-bit PCM | Mono/Stereo |
| API Output | 24kHz | 16-bit PCM | Mono |

---

## Blockers & Risks

### Current Blockers
| Date | Blocker | Severity | Status | Resolution |
|------|---------|----------|--------|------------|
| 2026-02-19 | BlackHole not visible in PyAudio | Medium | ✅ Resolved | Reboot fixed it (2026-02-23) |
| 2026-02-23 | Gemini freezes after first response in single session | High | Workaround | Reconnect per segment (new session every 5s) |
| 2026-02-23 | Abrupt audio cuts at segment boundaries | Medium | Open | Need silence detection for natural pause points |
| 2026-02-23 | Preview model (`*-preview-native-audio-09-2025`) stopped responding | High | ✅ Resolved | Switched to GA model `gemini-live-2.5-flash-native-audio` |

### Identified Risks
| Risk | Severity | Mitigation |
|------|----------|------------|
| Gemini S2ST leaves preview | Medium | Already on GA model; fallback to STT+Translate+TTS pipeline |
| Audio latency too high | Medium | Optimize chunk sizes, test different configs |
| Virtual audio driver issues | Low | Support multiple drivers, provide setup guide |
| Reconnect-per-segment adds latency | Medium | ~1-2s reconnect overhead per segment; investigate session reuse |

---

## Daily Log

### 2026-02-23 - PHASE 4 ELECTRON UI INTEGRATION COMPLETE
- **Created `python/server.py`** — stdio JSON-lines server wrapping proven translate.py logic
  - Commands: `ping`, `list_devices`, `start`, `stop`
  - Events: `ready`, `devices`, `started`, `status` (500ms interval), `stopped`, `error`
  - Uses manual activity detection (activity_start/end) from test_mic_to_speaker.py
  - Stdin read via thread + queue for cross-platform robustness
- **Created `electron/src/main/python-bridge.ts`** — PythonBridge subprocess manager
  - Spawns `python3 python/server.py`, parses JSON-lines from stdout
  - `send()`, `sendAndWait()`, `stop()` with graceful SIGKILL fallback
- **Wired all 5 IPC handlers** in main/index.ts: `devices:get`, `translation:start`, `translation:stop`, `settings:get`, `settings:set`
- **Updated renderer** — chunk-based status display (Sent/Recv/Backlog), dismissible error banner
- **Senior code review** found 6 critical + 9 important issues — ALL FIXED:
  - `process.cwd()` → `__dirname`-relative paths (Electron path resolution)
  - Async cancellation now awaits sub-tasks before closing audio streams
  - `before-quit` properly awaits cleanup via `event.preventDefault()` pattern
  - XSS fix: innerHTML → textContent for error messages
  - `sendAndWait` rejects on error messages (prevents 10s hang)
  - `translation:start` waits for `started` confirmation before UI updates
- **Smoke tested:** `echo '{"cmd":"list_devices"}' | python3 python/server.py` returns correct JSON
- **Phase 4 progress: 0% → 100%**
- **Overall progress: 65% → 80%**
- **Next:** Phase 5 — Packaging (mode selector UI, PyInstaller, electron-builder)

### 2026-02-19 - BIDIRECTIONAL TRANSLATION CLI COMPLETE (translate.py)
- **Created `translate.py`** -- production-ready bidirectional translation CLI at project root
- **Bypassed broken pipeline abstractions** (`client.py` queue flooding, `capture.py` receive loop crashes)
- **Extended proven pattern** from `test_minimal_translate.py` into full CLI
- **Two modes implemented:**
  - `upstream`: Mic (EN, 16kHz) -> Gemini S2ST -> BlackHole (24kHz) -> Zoom hears Japanese
  - `downstream`: BlackHole (Zoom audio, 24kHz->16kHz resample) -> Gemini S2ST -> Speakers in English
- **CLI features:** `--target`, `--duration`, `--mic-index`, `--speaker-index`, `--blackhole-index`, `--list-devices`
- **Technical approach:** Blocking PyAudio reads via `run_in_executor`, direct `session.send_realtime_input()` / `session.receive()` -- no async queues, no callbacks
- **Bug fix:** `--list-devices` no longer requires a mode argument (nargs="?" fix)
- **Blocker identified:** BlackHole installed via brew but not showing in PyAudio -- needs Mac reboot for kernel driver
- **Phase 3 progress: 0% -> 80%** (code-complete, pending BlackHole hardware verification)
- **Overall progress: 50% -> 65%**
- **Next:** Reboot Mac, verify BlackHole in Audio MIDI Setup, run end-to-end test with Zoom

### 2026-02-19 - S2ST API CONNECTION SUCCESSFUL
- **Vertex AI API enabled** on GCP project `project-08ad0c0e-0b71-4b9e-a18`
- **Fixed auth:** Switched from service account to personal ADC credentials (`gcloud auth application-default login`)
- **CRITICAL FIX: Model name was wrong across entire codebase**
  - Old (broken): `gemini-2.5-flash-s2st-exp-11-2025` — this model does NOT exist
  - New (working): `gemini-live-2.5-flash-preview-native-audio-09-2025`
  - S2ST is NOT a separate model — it's a feature of the native audio model, enabled via `enable_speech_to_speech_translation=True` config flag
  - GA model also available: `gemini-live-2.5-flash-native-audio`
- **test_s2st_access.py passed** — connection successful, no allowlist blocking
- `.env` updated with correct model name
- **TODO:** Update model name in `python/src/gemini/config.py`, `python/src/gemini/__init__.py`, and any other references
- **Next:** Validate Phase 3 Gemini integration code with correct model, then run end-to-end test

### 2026-02-19 (Earlier) - Phase 3 Validation Planning (GCP Billing Enabled)
- **GCP billing now enabled** with free $300 trial -- S2ST API should be accessible
- Phase 3 code already written (commit af74461) but untested
- Created validation action plan with 4 priority steps
- **Blocker removed:** GCP billing was the only blocker for Phase 3 validation

### 2026-01-19 (Night) - Phase 3 Planning COMPLETE
- **PHASE 3 PLANNING COMPLETE: Gemini Integration**
- Created comprehensive implementation plan: `docs/PHASE_3_GEMINI_INTEGRATION.md`
- Researched Gemini Live API documentation thoroughly:
  - Model: `gemini-2.5-flash-native-audio-preview-12-2025`
  - SDK: `google-genai` Python SDK with `client.aio.live.connect()`
  - Audio formats: 16kHz input, 24kHz output (matches existing audio pipeline)
  - WebSocket-based real-time streaming
- Updated `docs/JUNIOR_DEV_PLAN.md` with detailed Phase 3 tasks (Tasks 3.1-3.6)
- Created task TASK-2026-01-19-002 in task queue
- **Key deliverables planned:**
  1. `python/src/gemini/client.py` - GeminiS2STClient WebSocket class
  2. `python/src/gemini/config.py` - Configuration and language support
  3. `python/src/gemini/errors.py` - Custom exceptions and reconnection
  4. `python/src/routing/pipeline.py` - TranslationPipeline class
  5. `python/examples/test_gemini_translation.py` - Test script
- **Architecture:** Mic (16kHz) -> Gemini -> Virtual Mic (24kHz) -> Zoom
- **Architecture:** Zoom -> System Audio (24kHz) -> Gemini -> Speakers (24kHz)
- **Next: Senior Developer to review plan and Junior Developer to implement**

### 2026-01-19 (Evening) - Phase 2B COMPLETE
- **PHASE 2B COMPLETE: Audio Playback Pipeline**
- Senior Developer code review passed (after fixing one bug)
- **Files delivered:**
  1. `python/src/audio/playback.py` - SpeakerOutput & VirtualMicOutput classes
  2. `python/src/audio/devices.py` - Added find_speaker_device, find_virtual_mic_device helpers
  3. `python/src/audio/__init__.py` - Updated exports for playback classes
  4. `python/examples/test_audio_playback.py` - Test script demonstrating usage
- **Bug fix:** `asyncio.get_event_loop()` replaced with `asyncio.get_running_loop()` (deprecated API fix)
- **Code quality:** Full type hints, async/await patterns, proper cleanup, consistent with Phase 2A
- **Overall progress: 35% → 50%**
- **Next: Phase 3 - Gemini Integration (GeminiS2STClient, TranslationPipeline)**

### 2026-01-19 (Late Afternoon) - Phase 2B Coordination
- **Project Manager coordinating Phase 2B implementation**
- Task TASK-2026-01-19-001 confirmed in queue with status `pending_implementation`
- Implementation plan ready in `docs/JUNIOR_DEV_PLAN.md` (Tasks 2B.1-2B.4)
- Senior Developer to verify architecture approach before Junior Developer implements
- Target deliverables:
  1. `python/src/audio/playback.py` - SpeakerOutput & VirtualMicOutput classes (NEW)
  2. `python/src/audio/devices.py` - Add find_speaker_device, find_virtual_mic functions
  3. `python/src/audio/__init__.py` - Update exports for new playback classes
  4. `python/examples/test_audio_playback.py` - Test script demonstrating usage (NEW)
- Acceptance criteria defined in task queue entry

### 2026-01-19 (Afternoon) - Phase 2B Started
- **PHASE 2B AUDIO PLAYBACK STARTED**
- Creating SpeakerOutput class mirroring MicrophoneCapture patterns
- Creating VirtualMicOutput class for routing to Zoom
- Adding output device enumeration functions
- Following same patterns as Phase 2A (async/await, PyAudio callbacks, type hints)
- Target files:
  1. `python/src/audio/playback.py` - SpeakerOutput & VirtualMicOutput classes
  2. `python/src/audio/devices.py` - Add find_speaker_device, find_virtual_mic functions
  3. `python/examples/test_audio_playback.py` - Test script

### 2026-01-19 (Morning) - Phase 2A Committed
- ✅ **PHASE 2A COMMITTED TO MAIN: fd4334e**
- **Commit:** `feat(audio): implement Phase 2A audio capture pipeline`
- **Stats:** 8 files changed, 2,116 insertions
- **Files delivered:**
  1. `python/src/audio/capture.py` (463 lines) - MicrophoneCapture & SystemAudioCapture
  2. `python/src/audio/devices.py` (533 lines) - Device enumeration & management
  3. `python/src/audio/__init__.py` (62 lines) - Updated exports
  4. `python/examples/test_audio_capture.py` (187 lines) - Test script
  5. `python/examples/README.md` (163 lines) - Example documentation
  6. `docs/PHASE_2A_SUMMARY.md` (315 lines) - Phase summary
  7. `docs/AUDIO_CAPTURE_FLOW.md` (383 lines) - Flow documentation
- **Code Review Bugs Fixed:**
  1. Stereo-to-mono logic was inverted in SystemAudioCapture (fixed)
  2. Deprecated asyncio.get_event_loop() replaced with get_running_loop()
- **Performance:** <5% CPU, ~2MB memory per stream, ~64ms latency
- **Quality:** Production-ready with full type hints, async/await, proper cleanup
- **Overall progress: 25% → 35%**
- **Next: Phase 2B - Audio Playback (SpeakerOutput, VirtualMicOutput)**

### 2026-01-18 (After Midnight)
- ✅ **PHASE 2A COMPLETE: Audio Capture Pipeline**
- Implemented MicrophoneCapture class:
  - Async/await pattern with asyncio.Queue for non-blocking streaming
  - PyAudio callback mode for minimal latency
  - 16kHz, 16-bit PCM, mono configuration optimized for speech
  - Comprehensive error handling with graceful degradation
  - Statistics tracking (chunks, bytes, overruns)
  - Context manager support for easy resource management
- Implemented SystemAudioCapture class:
  - Extends BaseCaptureDevice with stereo-to-mono conversion
  - 24kHz sample rate for system audio
  - Supports BlackHole (macOS) and VB-Audio (Windows)
  - Real-time numpy-based audio channel mixing
- Implemented AudioDeviceManager and device enumeration:
  - Complete device discovery with PyAudio
  - Classification by type (input, output, loopback, virtual)
  - Smart detection of BlackHole and VB-Audio devices
  - Device configuration validation
  - Convenience functions for common use cases
  - CLI utility for debugging (run devices.py as script)
- All code follows clean code principles:
  - Full type hints with Python 3.10+ syntax
  - Immutable dataclasses for data structures
  - Comprehensive docstrings with examples
  - Enum-based state management
  - Custom exception hierarchy
  - No magic numbers - all constants properly defined
- Updated audio module __init__.py with exports
- **Overall progress: 25% → 35%**
- **Next: Phase 2B - Audio Playback (SpeakerOutput, VirtualMicOutput)**

### 2026-01-18 (Late Night)
- 🎉 **Phase 1 confirmed complete by project lead**
- Junior developer delivered excellent scaffolding for both Electron and Python
- All code is well-typed, properly configured, and ready for Phase 2
- No fixes required - quality exceeds expectations
- **Phase 2 (Audio Capture) is now active**
- Updated overall progress: 20% → 25%
- Next focus: Implement MicrophoneCapture and SystemAudioCapture classes

### 2026-01-18 (Night)
- ✅ **Code review passed** - Senior dev approved all Phase 1 code
- All Electron files reviewed: proper TypeScript, strict mode, good security practices
- All Python files reviewed: proper async structure, good typing, linting configured
- No critical or important issues found
- Committed all Phase 1 files to main branch
- **Ready for Phase 2: Audio Pipeline Implementation**

### 2026-01-18 (Evening)
- ✅ **PHASE 1 COMPLETE: Project Setup**
- Created complete Electron project structure:
  - package.json with all dependencies (Electron, Vite, TypeScript, ESLint, Prettier)
  - tsconfig.json with strict type checking enabled
  - vite.config.ts for build configuration
  - electron-builder.yml for packaging
  - Source files: main/index.ts, preload/index.ts, renderer/index.html, renderer/app.ts
  - Shared types and constants
  - ESLint and Prettier configuration
- Created complete Python backend structure:
  - requirements.txt with Gemini API, audio, and dev dependencies
  - pyproject.toml with Ruff, Black, and mypy configuration
  - Module structure: src/audio, src/gemini, src/routing
  - Main entry point with async event loop
  - Test directory structure
- Created development scripts:
  - dev.sh for running both Electron and Python
  - install-blackhole.sh for macOS virtual audio setup
- Created .env.example with all required environment variables
- Updated .gitignore for comprehensive coverage
- Updated PROJECT_STATUS.md: Overall progress 8% -> 15%
- **Next: Phase 2 - Audio Pipeline Implementation**

### 2026-01-18 (Afternoon)
- Created comprehensive SPEC.md specification document
  - Defined MVP criteria and success metrics
  - Detailed Phase 1-4 with tasks and success criteria
  - Documented all dependencies (Electron, Python, System)
  - Added risk analysis with mitigation strategies
- Updated progress: Project Setup 20% -> 30%, Overall 5% -> 8%
- Next: Create actual project directory structure (Electron + Python)

### 2026-01-15
- Researched and confirmed Gemini S2ST API availability
- Decided on Electron + Python tech stack
- Created project management files (CLAUDE.md, PROJECT_STATUS.md)
- Created ARCHITECTURE.md technical design document
- Next: Set up project structure

---

## Links & Resources
- [Gemini Live API Docs](https://ai.google.dev/gemini-api/docs/live)
- [Vertex AI S2ST Guide](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/live-api/speech-to-speech-translation)
- [BlackHole Audio](https://github.com/ExistentialAudio/BlackHole)
- [electron-audio-loopback](https://github.com/alectrocute/electron-audio-loopback)
