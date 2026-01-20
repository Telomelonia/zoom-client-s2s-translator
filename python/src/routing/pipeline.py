"""
Translation pipeline module.

Orchestrates bidirectional audio translation flow between audio devices
and Gemini Live API.
"""

import asyncio
import logging
from typing import Optional
from enum import Enum, auto
from dataclasses import dataclass

from ..audio import (
    MicrophoneCapture,
    SystemAudioCapture,
    SpeakerOutput,
    VirtualMicOutput,
    AudioCaptureError,
    AudioPlaybackError,
    find_virtual_mic_device,
    find_loopback_device,
    resample_audio,
    SAMPLE_RATE_SYSTEM,
    BIT_DEPTH,
    CHANNELS,
)
from ..gemini import (
    GeminiS2STClient,
    GeminiConfig,
    SupportedLanguage,
    GeminiConnectionError,
)

logger = logging.getLogger(__name__)


class PipelineMode(Enum):
    """Translation pipeline operating mode."""

    OUTGOING = auto()  # Mic -> Gemini -> Virtual Mic (for Zoom)
    INCOMING = auto()  # System Audio -> Gemini -> Speakers
    BIDIRECTIONAL = auto()  # Both simultaneously


class PipelineState(Enum):
    """Pipeline operational state."""

    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    ERROR = auto()


@dataclass
class PipelineStats:
    """Statistics for translation pipeline."""

    audio_chunks_captured: int = 0
    audio_chunks_sent_to_gemini: int = 0
    audio_chunks_received_from_gemini: int = 0
    audio_chunks_played: int = 0
    errors_encountered: int = 0
    current_mode: Optional[PipelineMode] = None


class TranslationPipelineError(Exception):
    """Base exception for translation pipeline errors."""

    pass


class TranslationPipeline:
    """
    Bidirectional real-time translation pipeline.

    Connects audio capture devices to Gemini S2ST API and routes
    translated audio to output devices. Supports three modes:

    1. OUTGOING: Your mic -> Gemini -> Virtual mic (for Zoom to hear)
    2. INCOMING: Zoom audio (system) -> Gemini -> Your speakers
    3. BIDIRECTIONAL: Both pipelines running simultaneously

    Example:
        ```python
        # Outgoing translation (your voice to Zoom in Japanese)
        config = GeminiConfig(target_language=SupportedLanguage.JAPANESE)
        pipeline = TranslationPipeline(config)

        async with pipeline:
            await pipeline.start_outgoing()
            # Speak into mic, translated audio goes to virtual mic
            await asyncio.sleep(60)  # Run for 1 minute
        ```
    """

    def __init__(
        self,
        config: GeminiConfig,
        mic_device_index: Optional[int] = None,
        speaker_device_index: Optional[int] = None,
        virtual_mic_device_index: Optional[int] = None,
        system_audio_device_index: Optional[int] = None,
    ):
        """
        Initialize translation pipeline.

        Args:
            config: Gemini configuration with target language
            mic_device_index: Microphone device index (None = default)
            speaker_device_index: Speaker device index (None = default)
            virtual_mic_device_index: Virtual mic device index (None = auto-detect)
            system_audio_device_index: System audio device index (None = auto-detect)
        """
        self._config = config

        # Audio devices
        self._mic_capture: Optional[MicrophoneCapture] = None
        self._system_capture: Optional[SystemAudioCapture] = None
        self._speaker_output: Optional[SpeakerOutput] = None
        self._virtual_mic_output: Optional[VirtualMicOutput] = None

        # Device indices
        self._mic_device_index = mic_device_index
        self._speaker_device_index = speaker_device_index
        self._virtual_mic_device_index = virtual_mic_device_index
        self._system_audio_device_index = system_audio_device_index

        # Gemini clients (separate for bidirectional to prevent audio mixing)
        self._gemini_client: Optional[GeminiS2STClient] = None  # Used for single-mode
        self._outgoing_gemini_client: Optional[GeminiS2STClient] = None  # For bidirectional outgoing
        self._incoming_gemini_client: Optional[GeminiS2STClient] = None  # For bidirectional incoming

        # Pipeline state
        self._state = PipelineState.STOPPED
        self._current_mode: Optional[PipelineMode] = None

        # Background tasks
        self._outgoing_send_task: Optional[asyncio.Task] = None
        self._outgoing_receive_task: Optional[asyncio.Task] = None
        self._incoming_send_task: Optional[asyncio.Task] = None
        self._incoming_receive_task: Optional[asyncio.Task] = None

        # Statistics
        self._stats = PipelineStats()

    @property
    def is_running(self) -> bool:
        """Check if pipeline is currently running."""
        return self._state == PipelineState.RUNNING

    @property
    def state(self) -> PipelineState:
        """Get current pipeline state."""
        return self._state

    @property
    def mode(self) -> Optional[PipelineMode]:
        """Get current operating mode."""
        return self._current_mode

    @property
    def stats(self) -> dict:
        """
        Get current pipeline statistics.

        Returns:
            Dictionary with pipeline statistics
        """
        stats = {
            "state": self._state.name,
            "mode": self._current_mode.name if self._current_mode else None,
            "audio_chunks_captured": self._stats.audio_chunks_captured,
            "audio_chunks_sent_to_gemini": self._stats.audio_chunks_sent_to_gemini,
            "audio_chunks_received_from_gemini": self._stats.audio_chunks_received_from_gemini,
            "audio_chunks_played": self._stats.audio_chunks_played,
            "errors_encountered": self._stats.errors_encountered,
        }

        # Add Gemini stats if client exists
        if self._current_mode == PipelineMode.BIDIRECTIONAL:
            if self._outgoing_gemini_client:
                stats["gemini_outgoing"] = self._outgoing_gemini_client.stats
            if self._incoming_gemini_client:
                stats["gemini_incoming"] = self._incoming_gemini_client.stats
        elif self._gemini_client:
            stats["gemini"] = self._gemini_client.stats

        return stats

    async def _initialize_gemini_client(self) -> None:
        """Initialize and connect single Gemini client (for outgoing or incoming mode)."""
        if self._gemini_client is None:
            self._gemini_client = GeminiS2STClient(config=self._config)
            await self._gemini_client.connect()
            logger.info("Gemini client connected")

    async def _initialize_bidirectional_clients(self) -> None:
        """Initialize and connect separate Gemini clients for bidirectional mode."""
        if self._outgoing_gemini_client is None:
            self._outgoing_gemini_client = GeminiS2STClient(config=self._config)
            await self._outgoing_gemini_client.connect()
            logger.info("Outgoing Gemini client connected")

        if self._incoming_gemini_client is None:
            self._incoming_gemini_client = GeminiS2STClient(config=self._config)
            await self._incoming_gemini_client.connect()
            logger.info("Incoming Gemini client connected")

    async def _run_outgoing_pipeline(self, gemini_client: Optional[GeminiS2STClient] = None) -> None:
        """
        Internal method to run outgoing pipeline without state checks.

        This is called by start_outgoing() and start_bidirectional().

        Args:
            gemini_client: Optional Gemini client to use (for bidirectional mode)
        """
        # Initialize microphone capture
        self._mic_capture = MicrophoneCapture(
            device_index=self._mic_device_index
        )
        await self._mic_capture.start()
        logger.info("Microphone capture started")

        # Initialize virtual mic output
        # Auto-detect device if not specified
        virtual_mic_index = self._virtual_mic_device_index
        if virtual_mic_index is None:
            virtual_mic_device = find_virtual_mic_device()
            if virtual_mic_device is None:
                raise TranslationPipelineError(
                    "Virtual microphone device not found. "
                    "Please install BlackHole (macOS) or VB-Audio (Windows) "
                    "and specify the device index."
                )
            virtual_mic_index = virtual_mic_device.index
            logger.info(f"Auto-detected virtual mic: {virtual_mic_device.name}")

        self._virtual_mic_output = VirtualMicOutput(
            device_index=virtual_mic_index
        )
        await self._virtual_mic_output.start()
        logger.info("Virtual microphone output started")

        # Start send and receive loops
        self._outgoing_send_task = asyncio.create_task(
            self._outgoing_send_loop(gemini_client)
        )
        self._outgoing_receive_task = asyncio.create_task(
            self._outgoing_receive_loop(gemini_client)
        )

    async def start_outgoing(self) -> None:
        """
        Start outgoing translation pipeline.

        Flow: Microphone -> Gemini API -> Virtual Microphone (for Zoom)

        Raises:
            TranslationPipelineError: If pipeline fails to start
        """
        if self.is_running:
            raise TranslationPipelineError("Pipeline is already running")

        self._state = PipelineState.STARTING
        self._current_mode = PipelineMode.OUTGOING
        logger.info("Starting outgoing translation pipeline")

        try:
            # Initialize Gemini client
            await self._initialize_gemini_client()

            # Run outgoing pipeline
            await self._run_outgoing_pipeline()

            self._state = PipelineState.RUNNING
            logger.info("Outgoing translation pipeline running")

        except Exception as e:
            self._state = PipelineState.ERROR
            self._stats.errors_encountered += 1
            logger.error(f"Failed to start outgoing pipeline: {e}")
            await self._cleanup_outgoing()
            raise TranslationPipelineError(f"Failed to start outgoing pipeline: {e}")

    async def _outgoing_send_loop(self, gemini_client: Optional[GeminiS2STClient] = None) -> None:
        """
        Send loop: Microphone -> Gemini API.

        Args:
            gemini_client: Optional Gemini client (uses self._gemini_client if not provided)
        """
        client = gemini_client or self._gemini_client
        try:
            async for audio_chunk in self._mic_capture.stream():
                # Send to Gemini
                await client.send_audio(audio_chunk.data)
                self._stats.audio_chunks_captured += 1
                self._stats.audio_chunks_sent_to_gemini += 1

        except asyncio.CancelledError:
            logger.debug("Outgoing send loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in outgoing send loop: {e}")
            self._stats.errors_encountered += 1
            self._state = PipelineState.ERROR

    async def _outgoing_receive_loop(self, gemini_client: Optional[GeminiS2STClient] = None) -> None:
        """
        Receive loop: Gemini API -> Virtual Microphone.

        Args:
            gemini_client: Optional Gemini client (uses self._gemini_client if not provided)
        """
        client = gemini_client or self._gemini_client
        try:
            async for audio_chunk in client.receive_audio():
                # Play to virtual mic
                await self._virtual_mic_output.write_chunk(audio_chunk)
                self._stats.audio_chunks_received_from_gemini += 1
                self._stats.audio_chunks_played += 1

        except asyncio.CancelledError:
            logger.debug("Outgoing receive loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in outgoing receive loop: {e}")
            self._stats.errors_encountered += 1
            self._state = PipelineState.ERROR

    async def _run_incoming_pipeline(self, gemini_client: Optional[GeminiS2STClient] = None) -> None:
        """
        Internal method to run incoming pipeline without state checks.

        This is called by start_incoming() and start_bidirectional().

        Args:
            gemini_client: Optional Gemini client to use (for bidirectional mode)
        """
        # Initialize system audio capture
        # Auto-detect device if not specified
        system_audio_index = self._system_audio_device_index
        if system_audio_index is None:
            loopback_device = find_loopback_device()
            if loopback_device is None:
                raise TranslationPipelineError(
                    "System audio loopback device not found. "
                    "Please install BlackHole (macOS) or VB-Audio (Windows) "
                    "and configure it for system audio capture, or specify the device index."
                )
            system_audio_index = loopback_device.index
            logger.info(f"Auto-detected loopback device: {loopback_device.name}")

        self._system_capture = SystemAudioCapture(
            device_index=system_audio_index
        )
        await self._system_capture.start()
        logger.info("System audio capture started")

        # Initialize speaker output
        self._speaker_output = SpeakerOutput(
            device_index=self._speaker_device_index
        )
        await self._speaker_output.start()
        logger.info("Speaker output started")

        # Start send and receive loops
        self._incoming_send_task = asyncio.create_task(
            self._incoming_send_loop(gemini_client)
        )
        self._incoming_receive_task = asyncio.create_task(
            self._incoming_receive_loop(gemini_client)
        )

    async def start_incoming(self) -> None:
        """
        Start incoming translation pipeline.

        Flow: System Audio (Zoom) -> Gemini API -> Speakers

        Raises:
            TranslationPipelineError: If pipeline fails to start
        """
        if self.is_running:
            raise TranslationPipelineError("Pipeline is already running")

        self._state = PipelineState.STARTING
        self._current_mode = PipelineMode.INCOMING
        logger.info("Starting incoming translation pipeline")

        try:
            # Initialize Gemini client
            await self._initialize_gemini_client()

            # Run incoming pipeline
            await self._run_incoming_pipeline()

            self._state = PipelineState.RUNNING
            logger.info("Incoming translation pipeline running")

        except Exception as e:
            self._state = PipelineState.ERROR
            self._stats.errors_encountered += 1
            logger.error(f"Failed to start incoming pipeline: {e}")
            await self._cleanup_incoming()
            raise TranslationPipelineError(f"Failed to start incoming pipeline: {e}")

    async def _incoming_send_loop(self, gemini_client: Optional[GeminiS2STClient] = None) -> None:
        """
        Send loop: System Audio -> Gemini API.

        Resamples system audio from 24kHz to 16kHz before sending to Gemini.

        Args:
            gemini_client: Optional Gemini client (uses self._gemini_client if not provided)
        """
        client = gemini_client or self._gemini_client
        try:
            async for audio_chunk in self._system_capture.stream():
                # Resample from 24kHz to 16kHz for Gemini
                # System audio is 24kHz but Gemini expects 16kHz input
                resampled_data = resample_audio(
                    audio_chunk.data,
                    original_rate=SAMPLE_RATE_SYSTEM,  # 24kHz
                    target_rate=GeminiS2STClient.INPUT_SAMPLE_RATE,  # 16kHz
                    channels=CHANNELS,
                    bit_depth=BIT_DEPTH,
                )

                # Send to Gemini
                await client.send_audio(resampled_data)
                self._stats.audio_chunks_captured += 1
                self._stats.audio_chunks_sent_to_gemini += 1

        except asyncio.CancelledError:
            logger.debug("Incoming send loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in incoming send loop: {e}")
            self._stats.errors_encountered += 1
            self._state = PipelineState.ERROR

    async def _incoming_receive_loop(self, gemini_client: Optional[GeminiS2STClient] = None) -> None:
        """
        Receive loop: Gemini API -> Speakers.

        Args:
            gemini_client: Optional Gemini client (uses self._gemini_client if not provided)
        """
        client = gemini_client or self._gemini_client
        try:
            async for audio_chunk in client.receive_audio():
                # Play to speakers
                await self._speaker_output.write_chunk(audio_chunk)
                self._stats.audio_chunks_received_from_gemini += 1
                self._stats.audio_chunks_played += 1

        except asyncio.CancelledError:
            logger.debug("Incoming receive loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in incoming receive loop: {e}")
            self._stats.errors_encountered += 1
            self._state = PipelineState.ERROR

    async def start_bidirectional(self) -> None:
        """
        Start bidirectional translation pipeline.

        Runs both outgoing and incoming pipelines concurrently with separate
        Gemini clients to prevent audio mixing.

        Raises:
            TranslationPipelineError: If pipeline fails to start
        """
        if self.is_running:
            raise TranslationPipelineError("Pipeline is already running")

        self._state = PipelineState.STARTING
        self._current_mode = PipelineMode.BIDIRECTIONAL
        logger.info("Starting bidirectional translation pipeline")

        try:
            # Initialize separate Gemini clients for bidirectional mode
            await self._initialize_bidirectional_clients()

            # Run both pipelines concurrently using separate clients
            await asyncio.gather(
                self._run_outgoing_pipeline(self._outgoing_gemini_client),
                self._run_incoming_pipeline(self._incoming_gemini_client)
            )

            self._state = PipelineState.RUNNING
            logger.info("Bidirectional translation pipeline running")

        except Exception as e:
            self._state = PipelineState.ERROR
            self._stats.errors_encountered += 1
            logger.error(f"Failed to start bidirectional pipeline: {e}")
            await self.stop()
            raise TranslationPipelineError(
                f"Failed to start bidirectional pipeline: {e}"
            )

    async def _cleanup_outgoing(self) -> None:
        """Clean up outgoing pipeline resources."""
        # Cancel tasks
        if self._outgoing_send_task and not self._outgoing_send_task.done():
            self._outgoing_send_task.cancel()
            try:
                await self._outgoing_send_task
            except asyncio.CancelledError:
                pass

        if self._outgoing_receive_task and not self._outgoing_receive_task.done():
            self._outgoing_receive_task.cancel()
            try:
                await self._outgoing_receive_task
            except asyncio.CancelledError:
                pass

        # Stop audio devices
        if self._mic_capture:
            await self._mic_capture.stop()
            self._mic_capture = None

        if self._virtual_mic_output:
            await self._virtual_mic_output.stop()
            self._virtual_mic_output = None

    async def _cleanup_incoming(self) -> None:
        """Clean up incoming pipeline resources."""
        # Cancel tasks
        if self._incoming_send_task and not self._incoming_send_task.done():
            self._incoming_send_task.cancel()
            try:
                await self._incoming_send_task
            except asyncio.CancelledError:
                pass

        if self._incoming_receive_task and not self._incoming_receive_task.done():
            self._incoming_receive_task.cancel()
            try:
                await self._incoming_receive_task
            except asyncio.CancelledError:
                pass

        # Stop audio devices
        if self._system_capture:
            await self._system_capture.stop()
            self._system_capture = None

        if self._speaker_output:
            await self._speaker_output.stop()
            self._speaker_output = None

    async def stop(self) -> None:
        """
        Stop the translation pipeline and clean up all resources.
        """
        if self._state == PipelineState.STOPPED:
            return

        self._state = PipelineState.STOPPING
        logger.info("Stopping translation pipeline")

        try:
            # Clean up based on mode
            if self._current_mode in (
                PipelineMode.OUTGOING,
                PipelineMode.BIDIRECTIONAL,
            ):
                await self._cleanup_outgoing()

            if self._current_mode in (
                PipelineMode.INCOMING,
                PipelineMode.BIDIRECTIONAL,
            ):
                await self._cleanup_incoming()

            # Disconnect Gemini client(s)
            if self._gemini_client:
                await self._gemini_client.disconnect()
                self._gemini_client = None

            if self._outgoing_gemini_client:
                await self._outgoing_gemini_client.disconnect()
                self._outgoing_gemini_client = None

            if self._incoming_gemini_client:
                await self._incoming_gemini_client.disconnect()
                self._incoming_gemini_client = None

            self._state = PipelineState.STOPPED
            self._current_mode = None
            logger.info("Translation pipeline stopped")

        except Exception as e:
            logger.error(f"Error stopping pipeline: {e}")
            self._stats.errors_encountered += 1
            self._state = PipelineState.ERROR

    # Context manager support
    async def __aenter__(self) -> "TranslationPipeline":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()
