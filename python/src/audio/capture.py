"""
Audio capture module.

Provides classes for capturing audio from microphone and system audio sources.
Uses PyAudio with async queues for non-blocking real-time streaming.
"""

import asyncio
import logging
from typing import Optional, Callable, Awaitable, AsyncGenerator
from dataclasses import dataclass
from enum import Enum, auto

import pyaudio
import numpy as np

from . import (
    SAMPLE_RATE_MIC,
    SAMPLE_RATE_SYSTEM,
    CHANNELS,
    CHUNK_SIZE,
    BIT_DEPTH,
)

logger = logging.getLogger(__name__)


class CaptureState(Enum):
    """Audio capture state."""

    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    ERROR = auto()


@dataclass(frozen=True)
class AudioChunk:
    """Immutable audio data chunk."""

    data: bytes
    timestamp: float
    sample_rate: int
    channels: int
    frames: int

    @property
    def duration_ms(self) -> float:
        """Calculate chunk duration in milliseconds."""
        return (self.frames / self.sample_rate) * 1000


class AudioCaptureError(Exception):
    """Base exception for audio capture errors."""

    pass


class AudioDeviceError(AudioCaptureError):
    """Audio device not found or unavailable."""

    pass


class AudioStreamError(AudioCaptureError):
    """Error during audio streaming."""

    pass


class BaseCaptureDevice:
    """
    Base class for audio capture devices.

    Provides common functionality for both microphone and system audio capture.
    Uses callback mode for minimal latency and async queues for integration.
    """

    def __init__(
        self,
        sample_rate: int,
        chunk_size: int = CHUNK_SIZE,
        channels: int = CHANNELS,
        device_index: Optional[int] = None,
    ):
        """
        Initialize audio capture device.

        Args:
            sample_rate: Audio sample rate in Hz
            chunk_size: Number of frames per buffer
            channels: Number of audio channels (1=mono, 2=stereo)
            device_index: PyAudio device index (None = default device)
        """
        self._sample_rate = sample_rate
        self._chunk_size = chunk_size
        self._channels = channels
        self._device_index = device_index

        self._pyaudio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._state = CaptureState.STOPPED

        # Async queue for audio chunks
        self._queue: asyncio.Queue[AudioChunk] = asyncio.Queue(maxsize=100)

        # Optional callback for each audio chunk
        self._on_data: Optional[Callable[[AudioChunk], Awaitable[None]]] = None

        # Event loop reference for callback thread
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Statistics
        self._chunks_captured = 0
        self._bytes_captured = 0
        self._overruns = 0

    @property
    def state(self) -> CaptureState:
        """Current capture state."""
        return self._state

    @property
    def sample_rate(self) -> int:
        """Audio sample rate in Hz."""
        return self._sample_rate

    @property
    def is_running(self) -> bool:
        """Check if capture is currently running."""
        return self._state == CaptureState.RUNNING

    @property
    def stats(self) -> dict:
        """Get capture statistics."""
        return {
            "chunks_captured": self._chunks_captured,
            "bytes_captured": self._bytes_captured,
            "overruns": self._overruns,
            "queue_size": self._queue.qsize(),
        }

    def _audio_callback(
        self,
        in_data: bytes,
        frame_count: int,
        time_info: dict,
        status_flags: int,
    ) -> tuple[None, int]:
        """
        PyAudio callback executed in separate thread.

        This is called by PyAudio for each audio buffer. We need to be fast here
        to avoid audio glitches. We push data to an async queue for processing.

        Args:
            in_data: Audio data as bytes
            frame_count: Number of frames
            time_info: Timing information from PortAudio
            status_flags: Stream status flags

        Returns:
            Tuple of (None, continue_flag)
        """
        # Check for input overflow (buffer overrun)
        if status_flags & pyaudio.paInputOverflow:
            self._overruns += 1
            logger.warning("Audio input overflow detected (buffer overrun)")

        try:
            # Create audio chunk
            chunk = AudioChunk(
                data=in_data,
                timestamp=time_info["input_buffer_adc_time"],
                sample_rate=self._sample_rate,
                channels=self._channels,
                frames=frame_count,
            )

            # Update statistics
            self._chunks_captured += 1
            self._bytes_captured += len(in_data)

            # Try to put in queue without blocking
            try:
                self._queue.put_nowait(chunk)
            except asyncio.QueueFull:
                self._overruns += 1
                logger.warning("Audio queue full, dropping chunk")

            # Schedule callback if registered
            if self._on_data and self._loop:
                asyncio.run_coroutine_threadsafe(self._on_data(chunk), self._loop)

        except Exception as e:
            logger.error(f"Error in audio callback: {e}")

        return (None, pyaudio.paContinue)

    async def start(
        self, on_data: Optional[Callable[[AudioChunk], Awaitable[None]]] = None
    ) -> None:
        """
        Start audio capture.

        Args:
            on_data: Optional async callback for each audio chunk

        Raises:
            AudioDeviceError: If device is not available
            AudioStreamError: If stream cannot be started
        """
        if self._state != CaptureState.STOPPED:
            raise AudioStreamError(f"Cannot start: already in {self._state} state")

        self._state = CaptureState.STARTING
        self._on_data = on_data
        self._loop = asyncio.get_running_loop()

        try:
            # Initialize PyAudio
            self._pyaudio = pyaudio.PyAudio()

            # Validate device
            if self._device_index is not None:
                try:
                    device_info = self._pyaudio.get_device_info_by_index(
                        self._device_index
                    )
                    logger.info(f"Using audio device: {device_info['name']}")
                except Exception as e:
                    raise AudioDeviceError(f"Invalid device index: {e}")

            # Open audio stream in callback mode
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,  # 16-bit PCM
                channels=self._channels,
                rate=self._sample_rate,
                input=True,
                input_device_index=self._device_index,
                frames_per_buffer=self._chunk_size,
                stream_callback=self._audio_callback,
                start=False,  # We'll start manually
            )

            # Start the stream
            self._stream.start_stream()
            self._state = CaptureState.RUNNING

            logger.info(
                f"Audio capture started: {self._sample_rate}Hz, "
                f"{self._channels}ch, {self._chunk_size} frames"
            )

        except Exception as e:
            self._state = CaptureState.ERROR
            await self._cleanup()
            raise AudioStreamError(f"Failed to start audio stream: {e}")

    async def stop(self) -> None:
        """
        Stop audio capture gracefully.

        This is idempotent - calling multiple times is safe.
        """
        if self._state == CaptureState.STOPPED:
            return

        self._state = CaptureState.STOPPING
        logger.info("Stopping audio capture...")

        await self._cleanup()

        self._state = CaptureState.STOPPED
        logger.info(f"Audio capture stopped. Stats: {self.stats}")

    async def _cleanup(self) -> None:
        """Clean up PyAudio resources."""
        try:
            if self._stream:
                if self._stream.is_active():
                    self._stream.stop_stream()
                self._stream.close()
                self._stream = None

            if self._pyaudio:
                self._pyaudio.terminate()
                self._pyaudio = None

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def read_chunk(self, timeout: Optional[float] = None) -> AudioChunk:
        """
        Read next audio chunk from queue.

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            AudioChunk with audio data

        Raises:
            asyncio.TimeoutError: If timeout expires
            AudioStreamError: If capture is not running
        """
        if self._state != CaptureState.RUNNING:
            raise AudioStreamError("Cannot read: capture is not running")

        if timeout:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        else:
            return await self._queue.get()

    async def stream(self) -> AsyncGenerator[AudioChunk, None]:
        """
        Async generator that yields audio chunks continuously.

        Yields:
            AudioChunk: Audio data chunks while capture is running

        Example:
            ```python
            async with MicrophoneCapture() as mic:
                async for chunk in mic.stream():
                    print(f"Received {len(chunk.data)} bytes")
            ```
        """
        while self.is_running:
            try:
                chunk = await self.read_chunk(timeout=1.0)
                if chunk:
                    yield chunk
            except asyncio.TimeoutError:
                # Timeout is expected, just check if we're still running
                continue
            except AudioStreamError:
                # Stream stopped
                break

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


class MicrophoneCapture(BaseCaptureDevice):
    """
    Captures audio from physical microphone.

    Optimized for speech input to Gemini S2ST API:
    - 16kHz sample rate (recommended for speech)
    - 16-bit PCM format
    - Mono channel
    - 1024 frame chunks for low latency

    Example:
        ```python
        async with MicrophoneCapture() as mic:
            while True:
                chunk = await mic.read_chunk()
                await send_to_translation_api(chunk.data)
        ```
    """

    def __init__(
        self,
        device_index: Optional[int] = None,
        sample_rate: int = SAMPLE_RATE_MIC,
        chunk_size: int = CHUNK_SIZE,
    ):
        """
        Initialize microphone capture.

        Args:
            device_index: PyAudio device index (None = default microphone)
            sample_rate: Sample rate in Hz (default: 16kHz for speech)
            chunk_size: Buffer size in frames (default: 1024)
        """
        super().__init__(
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            channels=CHANNELS,
            device_index=device_index,
        )
        logger.info("MicrophoneCapture initialized")


class SystemAudioCapture(BaseCaptureDevice):
    """
    Captures system audio output (loopback).

    Used to capture audio from Zoom or other applications.
    Requires virtual audio device (BlackHole on macOS, VB-Audio on Windows).

    Optimized for system audio:
    - 24kHz sample rate (Gemini recommendation for system audio)
    - 16-bit PCM format
    - Mono or stereo (auto-converted to mono)
    - 1024 frame chunks

    Example:
        ```python
        # Assumes BlackHole 2ch is configured as device
        async with SystemAudioCapture(device_index=5) as system:
            while True:
                chunk = await system.read_chunk()
                await send_to_translation_api(chunk.data)
        ```
    """

    def __init__(
        self,
        device_index: int,
        sample_rate: int = SAMPLE_RATE_SYSTEM,
        chunk_size: int = CHUNK_SIZE,
        stereo_to_mono: bool = True,
    ):
        """
        Initialize system audio capture.

        Args:
            device_index: PyAudio device index for loopback device (required)
            sample_rate: Sample rate in Hz (default: 24kHz)
            chunk_size: Buffer size in frames (default: 1024)
            stereo_to_mono: Convert stereo to mono by averaging channels
        """
        # System audio might be stereo, we'll handle conversion
        self._stereo_to_mono = stereo_to_mono
        # Capture stereo (2ch) when we want to convert to mono, otherwise mono (1ch)
        self._input_channels = 2 if stereo_to_mono else 1

        super().__init__(
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            channels=self._input_channels,
            device_index=device_index,
        )
        logger.info("SystemAudioCapture initialized")

    def _audio_callback(
        self,
        in_data: bytes,
        frame_count: int,
        time_info: dict,
        status_flags: int,
    ) -> tuple[None, int]:
        """
        Override callback to handle stereo-to-mono conversion.

        Args:
            in_data: Audio data as bytes
            frame_count: Number of frames
            time_info: Timing information
            status_flags: Stream status flags

        Returns:
            Tuple of (None, continue_flag)
        """
        # Convert stereo to mono if needed
        if self._stereo_to_mono and self._input_channels == 2:
            # Convert bytes to int16 array
            audio_array = np.frombuffer(in_data, dtype=np.int16)

            # Reshape to (frames, channels)
            audio_array = audio_array.reshape(-1, 2)

            # Average channels to get mono
            mono_array = audio_array.mean(axis=1).astype(np.int16)

            # Convert back to bytes
            in_data = mono_array.tobytes()

            # Update channels for the chunk
            original_channels = self._channels
            self._channels = 1

        result = super()._audio_callback(in_data, frame_count, time_info, status_flags)

        # Restore original channels value
        if self._stereo_to_mono and self._input_channels == 2:
            self._channels = original_channels

        return result
