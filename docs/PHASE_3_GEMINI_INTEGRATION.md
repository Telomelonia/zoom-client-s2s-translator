# Phase 3: Gemini Integration - Implementation Plan

> **Created:** 2026-01-19
> **Status:** Ready for Implementation
> **Prerequisites:** Phase 2A (Audio Capture) and Phase 2B (Audio Playback) complete

---

## Overview

Phase 3 integrates the Gemini Live API for real-time speech-to-speech translation. This phase connects the audio capture pipeline (Phase 2A) to Gemini's S2ST API and routes translated audio through the playback pipeline (Phase 2B).

### Architecture Summary

```
OUTGOING FLOW (Your voice -> Zoom):
  MicrophoneCapture (16kHz) -> GeminiS2STClient -> VirtualMicOutput (24kHz) -> Zoom

INCOMING FLOW (Zoom -> Your ears):
  SystemAudioCapture (24kHz) -> GeminiS2STClient -> SpeakerOutput (24kHz) -> Speakers
```

---

## Research Findings: Gemini Live API

### API Specifications

Based on official Google documentation and SDK references:

| Parameter | Value |
|-----------|-------|
| **Model** | `gemini-2.5-flash-native-audio-preview-12-2025` |
| **SDK** | `google-genai` Python SDK |
| **Connection** | WebSocket via `client.aio.live.connect()` |
| **Input Audio** | 16-bit PCM, 16kHz, mono |
| **Output Audio** | 16-bit PCM, 24kHz, mono |
| **Chunk Size** | 1024-2048 frames recommended |
| **Session Limit** | 10 minutes default |

### Key SDK Methods

```python
from google import genai
from google.genai import types

# Initialize client
client = genai.Client()

# Connect to Live API
async with client.aio.live.connect(model=MODEL, config=config) as session:
    # Send audio
    await session.send_realtime_input(
        audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
    )

    # Receive responses
    async for response in session.receive():
        # Process audio from response
        if response.server_content and response.server_content.model_turn:
            for part in response.server_content.model_turn.parts:
                if part.inline_data:
                    audio_data = part.inline_data.data
```

### LiveConnectConfig Options

```python
config = types.LiveConnectConfig(
    # Audio output only (no text)
    response_modalities=["AUDIO"],

    # Speech configuration with target language
    speech_config=types.SpeechConfig(
        language_code="ja-JP",  # Target language
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name="Charon"  # Optional voice selection
            )
        )
    ),

    # Transcription (optional but useful for debugging)
    input_audio_transcription=types.AudioTranscriptionConfig(),
    output_audio_transcription=types.AudioTranscriptionConfig(),

    # Enable affective dialog for more natural conversation
    enable_affective_dialog=True,

    # System instruction (optional)
    system_instruction="You are a real-time translator.",
)
```

### Supported Language Codes

The Gemini S2ST API supports 24+ languages. Key codes for this application:

| Language | Code |
|----------|------|
| English (US) | `en-US` |
| Japanese | `ja-JP` |
| Spanish | `es-ES` |
| French | `fr-FR` |
| German | `de-DE` |
| Chinese (Mandarin) | `cmn-CN` |
| Hindi | `hi-IN` |
| Portuguese (Brazil) | `pt-BR` |
| Korean | `ko-KR` |
| Arabic | `ar-XA` |

---

## Implementation Plan

### Task 3.1: GeminiS2STClient Class

**File:** `python/src/gemini/client.py`

**Purpose:** WebSocket client for Gemini Live API speech-to-speech translation.

**Class Structure:**

```python
class GeminiS2STClient:
    """
    WebSocket client for Gemini Speech-to-Speech Translation API.

    Manages connection lifecycle, audio streaming, and response handling.
    Supports automatic reconnection and error recovery.
    """

    # Class constants
    DEFAULT_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
    INPUT_SAMPLE_RATE = 16000
    OUTPUT_SAMPLE_RATE = 24000

    def __init__(
        self,
        target_language: str = "ja-JP",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_transcription: bool = False,
    ): ...

    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def send_audio(self, audio_chunk: bytes) -> None: ...
    async def receive_audio(self) -> AsyncGenerator[bytes, None]: ...
    async def get_transcription(self) -> Optional[Tuple[str, str]]: ...

    # Properties
    @property
    def is_connected(self) -> bool: ...
    @property
    def stats(self) -> dict: ...
```

**Key Implementation Details:**

1. **Connection Management:**
   - Use `client.aio.live.connect()` with async context manager
   - Store session reference for send/receive operations
   - Track connection state with enum (DISCONNECTED, CONNECTING, CONNECTED, ERROR)

2. **Audio Streaming:**
   - Send chunks via `session.send_realtime_input(audio=...)`
   - Use MIME type `audio/pcm;rate=16000` for input
   - Receive via async generator from `session.receive()`

3. **Error Handling:**
   - Catch connection errors and log appropriately
   - Support reconnection with exponential backoff
   - Handle session timeout (10 minute limit)

4. **Statistics Tracking:**
   - Chunks sent/received
   - Bytes sent/received
   - Connection duration
   - Error count

**Acceptance Criteria:**
- [ ] Connects to Gemini Live API successfully
- [ ] Sends 16kHz PCM audio chunks
- [ ] Receives 24kHz PCM audio responses
- [ ] Handles disconnection gracefully
- [ ] Provides connection state property
- [ ] Tracks statistics (chunks, bytes, errors)
- [ ] Full type hints and docstrings
- [ ] Context manager support (__aenter__, __aexit__)

---

### Task 3.2: GeminiConfig and Language Support

**File:** `python/src/gemini/config.py`

**Purpose:** Configuration management for Gemini API settings.

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class SupportedLanguage(Enum):
    """Supported languages for S2ST translation."""
    ENGLISH_US = "en-US"
    JAPANESE = "ja-JP"
    SPANISH = "es-ES"
    FRENCH = "fr-FR"
    GERMAN = "de-DE"
    CHINESE_MANDARIN = "cmn-CN"
    HINDI = "hi-IN"
    PORTUGUESE_BR = "pt-BR"
    KOREAN = "ko-KR"
    ARABIC = "ar-XA"

@dataclass(frozen=True)
class GeminiConfig:
    """Immutable configuration for Gemini S2ST client."""
    target_language: SupportedLanguage
    model: str = "gemini-2.5-flash-native-audio-preview-12-2025"
    enable_transcription: bool = False
    enable_affective_dialog: bool = True
    voice_name: Optional[str] = None

def get_language_name(code: SupportedLanguage) -> str:
    """Get human-readable language name from code."""
    ...
```

**Acceptance Criteria:**
- [ ] SupportedLanguage enum with all target languages
- [ ] GeminiConfig immutable dataclass
- [ ] Validation for language codes
- [ ] Helper functions for language display names

---

### Task 3.3: TranslationPipeline Class

**File:** `python/src/routing/pipeline.py`

**Purpose:** Orchestrates the full translation flow between audio devices and Gemini API.

**Class Structure:**

```python
class TranslationPipeline:
    """
    Bidirectional translation pipeline.

    Connects audio capture devices to Gemini S2ST API and routes
    translated audio to output devices.

    Supports two modes:
    1. Outgoing: Mic -> Gemini -> Virtual Mic (for Zoom)
    2. Incoming: System Audio -> Gemini -> Speakers
    """

    def __init__(
        self,
        target_language: str = "ja-JP",
        mic_device_index: Optional[int] = None,
        speaker_device_index: Optional[int] = None,
        virtual_mic_device_index: Optional[int] = None,
        system_audio_device_index: Optional[int] = None,
    ): ...

    async def start_outgoing(self) -> None:
        """Start mic -> Gemini -> virtual mic pipeline."""
        ...

    async def start_incoming(self) -> None:
        """Start system audio -> Gemini -> speakers pipeline."""
        ...

    async def start_bidirectional(self) -> None:
        """Start both pipelines concurrently."""
        ...

    async def stop(self) -> None: ...

    @property
    def is_running(self) -> bool: ...
    @property
    def stats(self) -> dict: ...
```

**Implementation Flow - Outgoing Pipeline:**

```
1. MicrophoneCapture.start() - Begin capturing mic audio (16kHz)
2. GeminiS2STClient.connect() - Connect to Gemini API
3. VirtualMicOutput.start() - Prepare virtual mic output (24kHz)
4. Concurrent loops:
   a. Send loop: mic.read_chunk() -> gemini.send_audio()
   b. Receive loop: gemini.receive_audio() -> virtual_mic.write_chunk()
5. On stop: Clean up all resources
```

**Implementation Flow - Incoming Pipeline:**

```
1. SystemAudioCapture.start() - Capture Zoom audio (24kHz from BlackHole)
2. GeminiS2STClient.connect() - Connect to Gemini API
3. SpeakerOutput.start() - Prepare speaker output (24kHz)
4. Concurrent loops:
   a. Send loop: system.read_chunk() -> gemini.send_audio()
   b. Receive loop: gemini.receive_audio() -> speaker.write_chunk()
5. On stop: Clean up all resources
```

**Key Implementation Details:**

1. **Concurrent Operation:**
   - Use `asyncio.gather()` for concurrent send/receive loops
   - Use `asyncio.create_task()` for background operations
   - Proper cancellation handling with try/except/finally

2. **Audio Format Handling:**
   - Input from mic: 16kHz (matches Gemini input requirement)
   - Input from system: 24kHz (may need resampling)
   - Output to speakers: 24kHz (matches Gemini output)
   - Output to virtual mic: 24kHz

3. **Error Recovery:**
   - Detect disconnections and attempt reconnection
   - Queue audio during reconnection (with size limit)
   - Log errors without crashing entire pipeline

4. **Latency Optimization:**
   - Use small chunk sizes (1024 frames)
   - Minimize queue depths
   - Pre-buffer output to prevent underruns

**Acceptance Criteria:**
- [ ] Outgoing pipeline: Mic -> Gemini -> Virtual Mic working
- [ ] Incoming pipeline: System Audio -> Gemini -> Speakers working
- [ ] Bidirectional mode runs both concurrently
- [ ] Graceful shutdown with resource cleanup
- [ ] Error handling with recovery attempts
- [ ] Statistics for monitoring performance
- [ ] Context manager support

---

### Task 3.4: Error Handling and Reconnection Logic

**File:** `python/src/gemini/errors.py`

**Purpose:** Custom exceptions and error handling utilities.

```python
class GeminiError(Exception):
    """Base exception for Gemini-related errors."""
    pass

class GeminiConnectionError(GeminiError):
    """Failed to connect to Gemini API."""
    pass

class GeminiAuthenticationError(GeminiError):
    """Authentication failed (invalid credentials)."""
    pass

class GeminiRateLimitError(GeminiError):
    """Rate limit exceeded."""
    pass

class GeminiSessionExpiredError(GeminiError):
    """Session timeout (10 minute limit)."""
    pass

class GeminiAudioError(GeminiError):
    """Error processing audio data."""
    pass
```

**Reconnection Strategy:**

```python
class ReconnectionHandler:
    """Handles automatic reconnection with exponential backoff."""

    MAX_RETRIES = 5
    BASE_DELAY = 1.0  # seconds
    MAX_DELAY = 30.0  # seconds

    async def reconnect_with_backoff(
        self,
        connect_func: Callable[[], Awaitable[None]],
    ) -> bool:
        """
        Attempt reconnection with exponential backoff.

        Returns True if reconnection successful, False if max retries exceeded.
        """
        ...
```

**Acceptance Criteria:**
- [ ] Custom exception hierarchy
- [ ] Exponential backoff reconnection
- [ ] Session expiry detection and handling
- [ ] Graceful degradation on persistent errors

---

### Task 3.5: Test Scripts and Examples

**File:** `python/examples/test_gemini_translation.py`

**Purpose:** Example script demonstrating Gemini S2ST integration.

```python
"""
Test script for Gemini Speech-to-Speech Translation.

Usage:
    python examples/test_gemini_translation.py --target ja-JP

Requirements:
    - GOOGLE_API_KEY environment variable set
    - Microphone access
    - Speaker output
"""

async def test_connection():
    """Test basic API connectivity."""
    ...

async def test_outgoing_translation():
    """Test mic -> Gemini -> speakers (for development)."""
    ...

async def test_full_pipeline():
    """Test complete bidirectional translation."""
    ...
```

**Acceptance Criteria:**
- [ ] Connection test (API key validation)
- [ ] Basic translation test (mic -> speakers)
- [ ] Language selection from command line
- [ ] Clear error messages for common issues
- [ ] Usage documentation in script

---

## File Structure After Phase 3

```
python/src/gemini/
    __init__.py          # Updated with new exports
    client.py            # GeminiS2STClient class
    config.py            # GeminiConfig, SupportedLanguage
    errors.py            # Custom exceptions

python/src/routing/
    __init__.py          # Updated with new exports
    pipeline.py          # TranslationPipeline class

python/examples/
    test_gemini_translation.py  # Test and demo script
```

---

## Dependencies

Ensure these are in `requirements.txt`:

```
# Already present
google-generativeai>=0.8.0
google-cloud-aiplatform>=1.38.0

# May need to add/update
google-genai>=1.0.0  # New unified SDK
```

Note: The `google-genai` package is the new unified SDK that provides `client.aio.live.connect()`.

---

## Environment Setup

Required environment variables:

```bash
# Option 1: API Key (simpler for development)
export GOOGLE_API_KEY=your-api-key

# Option 2: Service Account (recommended for production)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

---

## Testing Strategy

### Unit Tests

1. **GeminiS2STClient:**
   - Mock WebSocket connection
   - Test send/receive operations
   - Test error handling
   - Test statistics tracking

2. **TranslationPipeline:**
   - Mock audio devices and Gemini client
   - Test pipeline lifecycle
   - Test concurrent operations
   - Test error recovery

### Integration Tests

1. **API Connection Test:**
   - Verify credentials work
   - Test basic send/receive
   - Check for rate limits

2. **Audio Quality Test:**
   - Record test audio
   - Send through pipeline
   - Verify output quality

### Manual Testing Checklist

- [ ] Speak into mic, hear translation through speakers
- [ ] Test with multiple languages
- [ ] Test 10+ minute sessions (session renewal)
- [ ] Test network disconnection recovery
- [ ] Test with headphones (avoid feedback)

---

## Estimated Effort

| Task | Complexity | Est. Hours |
|------|------------|------------|
| 3.1 GeminiS2STClient | Medium | 4-6 |
| 3.2 Config & Languages | Small | 1-2 |
| 3.3 TranslationPipeline | Large | 6-8 |
| 3.4 Error Handling | Medium | 2-3 |
| 3.5 Test Scripts | Medium | 2-3 |
| **Total** | | **15-22** |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| API changes (preview) | Pin SDK version, monitor changelog |
| Rate limits | Implement backoff, consider quotas |
| Session timeout (10 min) | Auto-reconnect before timeout |
| Audio format mismatch | Validate formats, add resampling |
| High latency | Optimize chunk sizes, monitor metrics |

---

## Success Criteria for Phase 3

1. **Functional:**
   - Can speak into microphone and hear translated audio
   - Supports at least English, Japanese, Spanish, French
   - Handles 5+ minute continuous operation

2. **Quality:**
   - Translation latency < 1 second
   - No audio artifacts or glitches
   - Clean shutdown without resource leaks

3. **Robustness:**
   - Recovers from network interruptions
   - Handles API errors gracefully
   - Clear error messages for troubleshooting

---

## References

- [Gemini Live API Documentation](https://ai.google.dev/gemini-api/docs/live)
- [Google GenAI Python SDK](https://github.com/googleapis/python-genai)
- [Live API WebSocket Reference](https://ai.google.dev/api/live)
- [GenAI Processors Examples](https://github.com/google-gemini/genai-processors)
