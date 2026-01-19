# Task Queue

> Communication channel between Project Manager and Senior Developer

## How This Works

1. **Project Manager** creates tasks here when user requests require code changes
2. **Senior Developer** monitors this queue for pending tasks
3. Tasks flow through the status lifecycle until completion
4. Once completed, **Project Manager** closes tasks and updates documentation

## Active Tasks

### TASK-2026-01-19-001: Implement Phase 2B - Audio Playback Pipeline

| Field | Value |
|-------|-------|
| **ID** | TASK-2026-01-19-001 |
| **Status** | pending_senior_review |
| **Created** | 2026-01-19 |
| **Created By** | @project-manager |
| **Assigned To** | @senior-developer |
| **Priority** | High |

**Description:**
Implement the audio playback pipeline (Phase 2B) to complement the audio capture pipeline (Phase 2A). This includes:
1. SpeakerOutput class - plays translated audio to physical speakers
2. VirtualMicOutput class - routes audio to virtual microphone for Zoom input
3. Output device enumeration functions
4. Test examples demonstrating usage

The implementation must follow the exact same patterns as Phase 2A (async/await, PyAudio callbacks, type hints, immutable dataclasses, enum-based state management).

**Acceptance Criteria:**
- [ ] SpeakerOutput class implemented with async queue-based playback
- [ ] VirtualMicOutput class implemented for BlackHole/VB-Audio routing
- [ ] find_speaker_device() convenience function added
- [ ] find_virtual_mic_device() convenience function added
- [ ] test_audio_playback.py example script created
- [ ] All code has full type hints and docstrings
- [ ] Context manager support (__aenter__, __aexit__)
- [ ] Statistics tracking (chunks played, bytes played, underruns)
- [ ] Audio module __init__.py updated with new exports

**Context/Background:**
- Phase 2A completed with MicrophoneCapture and SystemAudioCapture (commit fd4334e)
- Playback classes should mirror the capture class patterns for consistency
- Output format: 24kHz PCM, 16-bit, mono (matches Gemini API output)
- Virtual mic is used to send translated audio INTO Zoom calls

**Files Likely Affected:**
- `python/src/audio/playback.py` (NEW)
- `python/src/audio/devices.py` (UPDATE - add convenience functions)
- `python/src/audio/__init__.py` (UPDATE - add exports)
- `python/examples/test_audio_playback.py` (NEW)

---

**Senior Developer Notes:**
Implementation plan created in JUNIOR_DEV_PLAN.md. Follow the established patterns from capture.py exactly.

**Implementation Plan Link:**
See `docs/JUNIOR_DEV_PLAN.md` - Phase 2B section

**Completion Notes:**
_To be filled when task is completed_

| Commit Hash | Files Changed | Completed Date |
|-------------|---------------|----------------|
| | | |

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
