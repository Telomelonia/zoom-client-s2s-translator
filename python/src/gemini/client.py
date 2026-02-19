"""
Gemini Live API client module.

WebSocket client for real-time speech-to-speech translation using
Google's Gemini Live API with native audio support.
"""

import asyncio
import logging
import os
from typing import Optional, AsyncGenerator
from enum import Enum, auto
from dataclasses import dataclass

from google import genai
from google.genai import types

from .config import GeminiConfig, SupportedLanguage
from .errors import (
    GeminiConnectionError,
    GeminiAuthenticationError,
    GeminiAudioError,
    GeminiSessionExpiredError,
    ReconnectionHandler,
    SessionTimeoutTracker,
)

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection state."""

    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    RECONNECTING = auto()
    ERROR = auto()


@dataclass
class GeminiStats:
    """Statistics for Gemini API session."""

    chunks_sent: int = 0
    chunks_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    connection_duration: float = 0.0
    error_count: int = 0
    reconnection_count: int = 0

    # Token usage estimation (Live API charges ~25 tokens/second of audio)
    TOKENS_PER_SECOND_AUDIO: int = 25

    @property
    def audio_seconds_sent(self) -> float:
        """Estimate audio seconds sent (16kHz, 16-bit mono = 32000 bytes/sec)."""
        return self.bytes_sent / 32000.0

    @property
    def audio_seconds_received(self) -> float:
        """Estimate audio seconds received (24kHz, 16-bit mono = 48000 bytes/sec)."""
        return self.bytes_received / 48000.0

    @property
    def estimated_input_tokens(self) -> int:
        """Estimate input tokens (25 tokens/second of audio)."""
        return int(self.audio_seconds_sent * self.TOKENS_PER_SECOND_AUDIO)

    @property
    def estimated_output_tokens(self) -> int:
        """Estimate output tokens (25 tokens/second of audio)."""
        return int(self.audio_seconds_received * self.TOKENS_PER_SECOND_AUDIO)

    @property
    def estimated_total_tokens(self) -> int:
        """Estimate total tokens used."""
        return self.estimated_input_tokens + self.estimated_output_tokens


class GeminiS2STClient:
    """
    WebSocket client for Gemini Speech-to-Speech Translation API.

    Manages connection lifecycle, audio streaming, and response handling
    with automatic reconnection and error recovery.

    Example:
        ```python
        config = GeminiConfig.from_env(target_language=SupportedLanguage.JAPANESE)
        client = GeminiS2STClient(config)

        async with client:
            # Send audio chunk
            await client.send_audio(audio_bytes)

            # Receive translated audio
            async for audio_chunk in client.receive_audio():
                # Play audio_chunk
                pass
        ```
    """

    # Audio format constants
    INPUT_SAMPLE_RATE = 16000  # Hz
    OUTPUT_SAMPLE_RATE = 24000  # Hz
    INPUT_MIME_TYPE = "audio/pcm;rate=16000"

    def __init__(
        self,
        config: GeminiConfig,
        enable_auto_reconnect: bool = True,
    ):
        """
        Initialize Gemini S2ST client for Vertex AI.

        Args:
            config: Gemini configuration with target language and settings
            enable_auto_reconnect: Enable automatic reconnection on failures

        Note:
            Authentication uses Google Cloud Application Default Credentials (ADC).
            Run `gcloud auth application-default login` or set
            GOOGLE_APPLICATION_CREDENTIALS environment variable.
        """
        self._config = config
        self._enable_auto_reconnect = enable_auto_reconnect

        # Vertex AI configuration
        self._gcp_project = config.gcp_project or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self._gcp_location = config.gcp_location

        if not self._gcp_project:
            raise GeminiAuthenticationError(
                "No GCP project provided. Set GOOGLE_CLOUD_PROJECT environment variable "
                "or pass gcp_project in GeminiConfig."
            )

        # Client and session
        self._client: Optional[genai.Client] = None
        self._session_context = None  # Async context manager
        self._session = None  # Session from context
        self._state = ConnectionState.DISCONNECTED

        # Reconnection and timeout handling
        self._reconnection_handler = ReconnectionHandler()
        self._timeout_tracker = SessionTimeoutTracker()

        # Statistics
        self._stats = GeminiStats()
        self._connection_start_time: Optional[float] = None

        # Receive queue for audio chunks
        self._receive_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=100)
        self._receive_task: Optional[asyncio.Task] = None

        # Transcription buffers (if enabled)
        self._input_transcription: list[str] = []
        self._output_transcription: list[str] = []

    @property
    def is_connected(self) -> bool:
        """Check if currently connected to Gemini API."""
        return self._state == ConnectionState.CONNECTED and self._session is not None

    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def stats(self) -> dict:
        """
        Get current session statistics including token usage estimates.

        Returns:
            Dictionary with connection stats (chunks, bytes, duration, errors, tokens)

        Note:
            Token estimates are based on ~25 tokens/second of audio.
            S2ST preview is currently FREE but this helps track usage for when it goes GA.
        """
        if self._connection_start_time:
            loop = asyncio.get_running_loop()
            self._stats.connection_duration = (
                loop.time() - self._connection_start_time
            )

        return {
            "chunks_sent": self._stats.chunks_sent,
            "chunks_received": self._stats.chunks_received,
            "bytes_sent": self._stats.bytes_sent,
            "bytes_received": self._stats.bytes_received,
            "connection_duration": self._stats.connection_duration,
            "error_count": self._stats.error_count,
            "reconnection_count": self._stats.reconnection_count,
            "state": self._state.name,
            # Token usage estimates (for cost tracking when S2ST leaves preview)
            "audio_seconds_sent": round(self._stats.audio_seconds_sent, 2),
            "audio_seconds_received": round(self._stats.audio_seconds_received, 2),
            "estimated_input_tokens": self._stats.estimated_input_tokens,
            "estimated_output_tokens": self._stats.estimated_output_tokens,
            "estimated_total_tokens": self._stats.estimated_total_tokens,
        }

    def _create_live_config(self) -> types.LiveConnectConfig:
        """
        Create LiveConnectConfig from GeminiConfig.

        Returns:
            LiveConnectConfig object for API connection
        """
        # Speech configuration with target language
        speech_config = types.SpeechConfig(
            language_code=self._config.language_code
        )

        # Optional voice configuration
        if self._config.voice_name:
            speech_config.voice_config = types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=self._config.voice_name
                )
            )

        # Build config (matches the working test_s2st_access.py pattern)
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=speech_config,
        )

        # Optional transcription
        if self._config.enable_transcription:
            config.input_audio_transcription = types.AudioTranscriptionConfig()
            config.output_audio_transcription = types.AudioTranscriptionConfig()

        # Optional system instruction
        if self._config.system_instruction:
            config.system_instruction = self._config.system_instruction

        return config

    async def connect(self) -> None:
        """
        Establish connection to Gemini Live API.

        Raises:
            GeminiAuthenticationError: If API key is invalid
            GeminiConnectionError: If connection fails
        """
        if self.is_connected:
            logger.warning("Already connected to Gemini API")
            return

        self._state = ConnectionState.CONNECTING
        logger.info(
            f"Connecting to Gemini Live API with model {self._config.model}"
        )

        try:
            # Initialize Vertex AI client (uses ADC for authentication)
            self._client = genai.Client(
                vertexai=True,
                project=self._gcp_project,
                location=self._gcp_location,
            )

            # Create live config
            live_config = self._create_live_config()

            # Connect to Live API (returns async context manager)
            self._session_context = self._client.aio.live.connect(
                model=self._config.model, config=live_config
            )
            self._session = await self._session_context.__aenter__()

            # Mark connection as established
            self._state = ConnectionState.CONNECTED
            self._connection_start_time = asyncio.get_running_loop().time()
            self._timeout_tracker.start_session()

            # Start receive task
            self._receive_task = asyncio.create_task(self._receive_loop())

            logger.info(
                f"Connected to Gemini API. Target language: {self._config.language_display_name}"
            )

        except Exception as e:
            self._state = ConnectionState.ERROR
            self._stats.error_count += 1

            # Check for authentication errors
            if "authentication" in str(e).lower() or "api key" in str(e).lower():
                raise GeminiAuthenticationError(f"Authentication failed: {e}")

            raise GeminiConnectionError(f"Failed to connect to Gemini API: {e}")

    async def disconnect(self) -> None:
        """
        Disconnect from Gemini Live API and clean up resources.
        """
        if self._state == ConnectionState.DISCONNECTED:
            return

        logger.info("Disconnecting from Gemini API")

        # Cancel receive task
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        # Close session context
        if self._session_context:
            try:
                await self._session_context.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing session context: {e}")
            self._session_context = None
            self._session = None

        # Reset state
        self._state = ConnectionState.DISCONNECTED
        self._timeout_tracker.end_session()
        self._client = None

        logger.info("Disconnected from Gemini API")

    async def send_audio(self, audio_chunk: bytes) -> None:
        """
        Send audio chunk to Gemini API for translation.

        Args:
            audio_chunk: Raw PCM audio bytes (16-bit, 16kHz, mono)

        Raises:
            GeminiConnectionError: If not connected
            GeminiAudioError: If audio sending fails
        """
        if not self.is_connected:
            raise GeminiConnectionError("Not connected to Gemini API")

        try:
            # Create audio blob
            audio_blob = types.Blob(
                data=audio_chunk, mime_type=self.INPUT_MIME_TYPE
            )

            # Send to API
            await self._session.send_realtime_input(audio=audio_blob)

            # Update stats
            self._stats.chunks_sent += 1
            self._stats.bytes_sent += len(audio_chunk)

        except Exception as e:
            self._stats.error_count += 1
            logger.error(f"Failed to send audio: {e}")

            # Check for session expiry
            if "session" in str(e).lower() and "expired" in str(e).lower():
                raise GeminiSessionExpiredError(
                    "Session expired. Reconnection required."
                )

            raise GeminiAudioError(f"Failed to send audio chunk: {e}")

    async def _receive_loop(self) -> None:
        """
        Background task to receive responses from Gemini API.

        Processes incoming audio and optional transcriptions,
        placing audio chunks in the receive queue.
        """
        try:
            async for response in self._session.receive():
                # Process server content
                if response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        # Extract audio data
                        if part.inline_data:
                            audio_data = part.inline_data.data
                            self._stats.chunks_received += 1
                            self._stats.bytes_received += len(audio_data)

                            # Put in queue for consumer
                            await self._receive_queue.put(audio_data)

                        # Extract transcription (if enabled)
                        if part.text:
                            self._output_transcription.append(part.text)

                # Process input transcription (if enabled)
                input_transcription = getattr(response, "input_transcription", None)
                if self._config.enable_transcription and input_transcription:
                    self._input_transcription.append(
                        input_transcription.text
                    )

        except asyncio.CancelledError:
            logger.debug("Receive loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")
            self._state = ConnectionState.ERROR
            self._stats.error_count += 1

    async def receive_audio(self) -> AsyncGenerator[bytes, None]:
        """
        Receive translated audio chunks from Gemini API.

        Yields:
            Audio chunks as bytes (16-bit PCM, 24kHz, mono)

        Example:
            ```python
            async for audio_chunk in client.receive_audio():
                await speaker.write_chunk(audio_chunk)
            ```
        """
        if not self.is_connected:
            raise GeminiConnectionError("Not connected to Gemini API")

        while self.is_connected:
            try:
                # Wait for audio with timeout
                audio_chunk = await asyncio.wait_for(
                    self._receive_queue.get(), timeout=1.0
                )
                yield audio_chunk

            except asyncio.TimeoutError:
                # Check if session should be reconnected
                if self._timeout_tracker.should_reconnect():
                    logger.warning("Session timeout approaching, reconnecting...")
                    if self._enable_auto_reconnect:
                        await self._reconnect()
                    else:
                        raise GeminiSessionExpiredError(
                            "Session timeout approaching and auto-reconnect disabled"
                        )
                continue

            except Exception as e:
                logger.error(f"Error receiving audio: {e}")
                break

    async def _reconnect(self) -> None:
        """
        Internal method to handle reconnection with backoff.
        """
        self._state = ConnectionState.RECONNECTING
        self._stats.reconnection_count += 1

        # Disconnect first
        await self.disconnect()

        # Attempt reconnection with backoff
        success = await self._reconnection_handler.reconnect_with_backoff(
            self.connect
        )

        if not success:
            self._state = ConnectionState.ERROR
            raise GeminiConnectionError(
                "Failed to reconnect after multiple attempts"
            )

    def get_transcriptions(self) -> tuple[list[str], list[str]]:
        """
        Get accumulated transcriptions (if enabled).

        Returns:
            Tuple of (input_transcriptions, output_transcriptions)
        """
        return (self._input_transcription.copy(), self._output_transcription.copy())

    def clear_transcriptions(self) -> None:
        """Clear accumulated transcription buffers."""
        self._input_transcription.clear()
        self._output_transcription.clear()

    # Context manager support
    async def __aenter__(self) -> "GeminiS2STClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
