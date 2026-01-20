# Task Queue

> Communication channel between Project Manager and Senior Developer

## How This Works

1. **Project Manager** creates tasks here when user requests require code changes
2. **Senior Developer** monitors this queue for pending tasks
3. Tasks flow through the status lifecycle until completion
4. Once completed, **Project Manager** closes tasks and updates documentation

## Active Tasks

### TASK-2026-01-19-002: Implement Phase 3 - Gemini Integration

| Field | Value |
|-------|-------|
| **ID** | TASK-2026-01-19-002 |
| **Status** | pending_senior_review |
| **Created** | 2026-01-19 |
| **Created By** | @project-manager |
| **Assigned To** | @senior-developer |
| **Priority** | High |

**Description:**
Implement the Gemini Live API integration (Phase 3) to connect the audio capture/playback pipeline to Google's S2ST translation service. This includes:
1. GeminiS2STClient - WebSocket client for Gemini Live API
2. GeminiConfig - Configuration and language support
3. TranslationPipeline - Orchestrates audio devices and Gemini API
4. Error handling with reconnection logic
5. Test script demonstrating usage

The implementation enables real-time speech-to-speech translation for Zoom calls.

**Architecture:**
```
OUTGOING: Mic (16kHz) -> GeminiS2STClient -> Virtual Mic (24kHz) -> Zoom
INCOMING: Zoom -> System Audio (24kHz) -> GeminiS2STClient -> Speakers (24kHz)
```

**Acceptance Criteria:**
- [ ] GeminiS2STClient connects to Gemini Live API successfully
- [ ] Audio streaming works with `send_realtime_input()` method
- [ ] Audio receiving works with async generator pattern
- [ ] SupportedLanguage enum with 10+ languages (ja-JP, es-ES, fr-FR, etc.)
- [ ] GeminiConfig immutable dataclass for configuration
- [ ] TranslationPipeline supports outgoing, incoming, and bidirectional modes
- [ ] Auto-detection of virtual audio devices (BlackHole/VB-Audio)
- [ ] Custom exception hierarchy (GeminiError, GeminiConnectionError, etc.)
- [ ] ReconnectionHandler with exponential backoff
- [ ] Connection state tracking and statistics
- [ ] Context manager support for all classes
- [ ] Full type hints and docstrings
- [ ] Test script with CLI for language selection
- [ ] Module exports updated in __init__.py files

**Context/Background:**
- Phase 2A (Audio Capture) and Phase 2B (Audio Playback) are complete
- Audio formats match Gemini requirements: 16kHz input, 24kHz output
- Model: `gemini-2.5-flash-native-audio-preview-12-2025`
- SDK: `google-genai` Python package with `client.aio.live.connect()`
- WebSocket-based real-time streaming
- Session limit: 10 minutes (need reconnection handling)

**Files to Create:**
- `python/src/gemini/client.py` - GeminiS2STClient class
- `python/src/gemini/config.py` - GeminiConfig, SupportedLanguage
- `python/src/gemini/errors.py` - Custom exceptions, ReconnectionHandler
- `python/src/routing/pipeline.py` - TranslationPipeline class
- `python/examples/test_gemini_translation.py` - Test script

**Files to Update:**
- `python/src/gemini/__init__.py` - Add new exports
- `python/src/routing/__init__.py` - Add new exports
- `python/requirements.txt` - Ensure `google-genai` is included

---

**Senior Developer Notes:**
Full implementation plan available in `docs/PHASE_3_GEMINI_INTEGRATION.md`.
Detailed task breakdown in `docs/JUNIOR_DEV_PLAN.md` - Phase 3 section (Tasks 3.1-3.6).

**Implementation Plan Link:**
- `docs/PHASE_3_GEMINI_INTEGRATION.md` - Comprehensive plan with research findings
- `docs/JUNIOR_DEV_PLAN.md` - Task-by-task implementation guide

**Completion Notes:**
_To be filled when task is completed_

| Commit Hash | Files Changed | Completed Date |
|-------------|---------------|----------------|

---

## Completed Tasks Archive

### TASK-2026-01-19-001: Implement Phase 2B - Audio Playback Pipeline

| Field | Value |
|-------|-------|
| **ID** | TASK-2026-01-19-001 |
| **Status** | closed |
| **Created** | 2026-01-19 |
| **Completed** | 2026-01-19 |
| **Priority** | High |

**Description:**
Implemented audio playback pipeline with SpeakerOutput and VirtualMicOutput classes.

**Completion Notes:**
- All acceptance criteria met
- Bug fix applied: `asyncio.get_event_loop()` replaced with `asyncio.get_running_loop()`
- Code review passed by Senior Developer

| Commit Hash | Files Changed | Completed Date |
|-------------|---------------|----------------|
| ee72496 | 4 | 2026-01-19 |

## Task Status Legend

| Status | Description |
|--------|-------------|
| `pending_senior_review` | Waiting for Senior Developer to pick up |
| `in_progress_senior` | Senior Developer is planning/analyzing |
| `pending_implementation` | Plan ready, waiting for Junior Developer |
| `in_implementation` | Junior Developer working on it |
| `pending_code_review` | Code submitted, awaiting Senior review |
| `completed` | Done - PM to update docs and close |
| `closed` | Fully complete |

## Task Template

When creating a new task, copy this template:

```markdown
### TASK-YYYY-MM-DD-NNN: [Short Title]

| Field | Value |
|-------|-------|
| **ID** | TASK-YYYY-MM-DD-NNN |
| **Status** | pending_senior_review |
| **Created** | YYYY-MM-DD |
| **Created By** | @project-manager |
| **Assigned To** | @senior-developer |
| **Priority** | High / Medium / Low |

**Description:**
[Detailed description of what needs to be done]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Context/Background:**
[Any relevant context from user request or project status]

**Files Likely Affected:**
- `path/to/file1`
- `path/to/file2`

---

**Senior Developer Notes:**
_To be filled by Senior Developer during planning_

**Implementation Plan Link:**
_Link to JUNIOR_DEV_PLAN.md entry once created_

**Completion Notes:**
_To be filled when task is completed_

| Commit Hash | Files Changed | Completed Date |
|-------------|---------------|----------------|
| | | |
```

---

## Completed Tasks Archive

_Completed tasks are moved here after closure_

---

## Queue Management Rules

1. **One task at a time per developer** - Don't overload the queue
2. **Priority ordering** - Critical > High > Medium > Low
3. **Dependencies noted** - If Task B depends on Task A, note it clearly
4. **Status updates required** - Update status when transitioning
5. **Blockers escalated** - If blocked, mark status and notify PM
