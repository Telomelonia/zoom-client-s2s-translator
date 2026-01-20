"""
Audio playback module.

Provides classes for playing audio to speakers and virtual microphone devices.
Uses PyAudio with callback mode and queue.Queue for thread-safe audio streaming.

IMPORTANT: Uses queue.Queue (not asyncio.Queue) because PyAudio callbacks
run in a separate thread. Async wrappers are provided using run_in_executor.
"""

import asyncio
import logging
import queue
from typing import Optional
from enum import Enum, auto

import pyaudio

from . import (
    SAMPLE_RATE_OUTPUT,
    CHANNELS,
    CHUNK_SIZE,
    BIT_DEPTH,
)

logger = logging.getLogger(__name__)


class PlaybackState(Enum):
    """Audio playback state."""

    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    ERROR = auto()


class AudioPlaybackError(Exception):
    """Base exception for audio playback errors."""

    pass


class PlaybackDeviceError(AudioPlaybackError):
    """Playback device not found or unavailable."""

    pass


class PlaybackStreamError(AudioPlaybackError):
    """Error during audio playback streaming."""

    pass


class BasePlaybackDevice:
    """
    Base class for audio playback devices.

    Provides common functionality for both speaker and virtual mic output.
    Uses callback mode for minimal latency and queue.Queue for thread-safe integration.

    CRITICAL: Uses queue.Queue (standard library) instead of asyncio.Queue because
    PyAudio callbacks run in a separate thread. Async methods wrap using run_in_executor.
    """

    def __init__(
        self,
        sample_rate: int,
        chunk_size: int = CHUNK_SIZE,
        channels: int = CHANNELS,
        device_index: Optional[int] = None,
    ):
        """
        Initialize audio playback device.

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
        self._state = PlaybackState.STOPPED

        # Thread-safe queue for audio data (NOT asyncio.Queue!)
        # PyAudio callback runs in separate thread, so we need queue.Queue
        self._queue: queue.Queue[bytes] = queue.Queue(maxsize=100)

        # Event loop reference for async operations
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Statistics
        self._chunks_played = 0
        self._bytes_played = 0
        self._underruns = 0

        # Silence buffer for underruns
        bytes_per_chunk = chunk_size * channels * (BIT_DEPTH // 8)
        self._silence = bytes(bytes_per_chunk)

        # Pre-buffer with silence chunks for clean start (2-3 chunks)
        self._prebuffer_size = 2

    @property
    def state(self) -> PlaybackState:
        """Current playback state."""
        return self._state

    @property
    def sample_rate(self) -> int:
        """Audio sample rate in Hz."""
        return self._sample_rate

    @property
    def is_running(self) -> bool:
        """Check if playback is currently running."""
        return self._state == PlaybackState.RUNNING

    @property
    def stats(self) -> dict:
        """Get playback statistics."""
        return {
            "chunks_played": self._chunks_played,
            "bytes_played": self._bytes_played,
            "underruns": self._underruns,
            "queue_size": self._queue.qsize(),
        }

    def _audio_callback(
        self,
        in_data: bytes,
        frame_count: int,
        time_info: dict,
        status_flags: int,
    ) -> tuple[bytes, int]:
        """
        PyAudio callback executed in separate thread.

        This is called by PyAudio when it needs more audio data to play.
        We need to return data quickly to avoid audio glitches.

        CRITICAL: This runs in a separate thread, so we use queue.Queue.get_nowait()
        which is thread-safe, NOT asyncio.Queue.

        Args:
            in_data: Not used for output streams
            frame_count: Number of frames requested
            time_info: Timing information from PortAudio
            status_flags: Stream status flags

        Returns:
            Tuple of (audio_data, continue_flag)
        """
        # Check for output underflow (buffer underrun)
        if status_flags & pyaudio.paOutputUnderflow:
            self._underruns += 1
            logger.warning("Audio output underflow detected (buffer underrun)")

        try:
            # Try to get audio from queue without blocking
            try:
                audio_data = self._queue.get_nowait()
                self._chunks_played += 1
                self._bytes_played += len(audio_data)
            except queue.Empty:
                # No data available, play silence
                audio_data = self._silence
                self._underruns += 1

        except Exception as e:
            logger.error(f"Error in playback callback: {e}")
            audio_data = self._silence

        return (audio_data, pyaudio.paContinue)

    async def start(self) -> None:
        """
        Start audio playback.

        Pre-buffers silence chunks to prevent initial underruns.

        Raises:
            PlaybackDeviceError: If device is not available
            PlaybackStreamError: If stream cannot be started
        """
        if self._state != PlaybackState.STOPPED:
            raise PlaybackStreamError(f"Cannot start: already in {self._state} state")

        self._state = PlaybackState.STARTING
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
                    raise PlaybackDeviceError(f"Invalid device index: {e}")

            # Pre-buffer silence chunks to prevent initial underruns
            for _ in range(self._prebuffer_size):
                try:
                    self._queue.put_nowait(self._silence)
                except queue.Full:
                    pass  # Queue might be smaller than prebuffer size

            # Open audio stream in callback mode
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,  # 16-bit PCM
                channels=self._channels,
                rate=self._sample_rate,
                output=True,
                output_device_index=self._device_index,
                frames_per_buffer=self._chunk_size,
                stream_callback=self._audio_callback,
                start=False,  # We'll start manually
            )

            # Start the stream
            self._stream.start_stream()
            self._state = PlaybackState.RUNNING

            logger.info(
                f"Audio playback started: {self._sample_rate}Hz, "
                f"{self._channels}ch, {self._chunk_size} frames, "
                f"prebuffered {self._prebuffer_size} chunks"
            )

        except Exception as e:
            self._state = PlaybackState.ERROR
            await self._cleanup()
            raise PlaybackStreamError(f"Failed to start audio stream: {e}")

    async def stop(self) -> None:
        """
        Stop audio playback gracefully.

        This is idempotent - calling multiple times is safe.
        """
        if self._state == PlaybackState.STOPPED:
            return

        self._state = PlaybackState.STOPPING
        logger.info("Stopping audio playback...")

        await self._cleanup()

        self._state = PlaybackState.STOPPED
        logger.info(f"Audio playback stopped. Stats: {self.stats}")

    async def drain(self) -> None:
        """
        Wait for all queued audio to finish playing.

        Useful for clean shutdown after final audio chunk.
        Waits until queue is empty with a timeout.
        """
        if self._state != PlaybackState.RUNNING:
            return

        logger.info("Draining playback queue...")
        max_wait_seconds = 5.0
        poll_interval = 0.05

        start_time = asyncio.get_running_loop().time()

        while self._queue.qsize() > 0:
            elapsed = asyncio.get_running_loop().time() - start_time
            if elapsed > max_wait_seconds:
                logger.warning(f"Drain timeout after {max_wait_seconds}s")
                break

            await asyncio.sleep(poll_interval)

        logger.info("Playback queue drained")

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

            # Clear the queue
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def write_chunk(self, audio_data: bytes, timeout: Optional[float] = None) -> None:
        """
        Write audio data to playback queue (async version).

        Uses run_in_executor to wrap the blocking queue.put() call.

        Args:
            audio_data: Raw PCM audio bytes to play
            timeout: Maximum time to wait if queue is full (None = wait forever)

        Raises:
            asyncio.TimeoutError: If timeout expires
            PlaybackStreamError: If playback is not running
        """
        if self._state != PlaybackState.RUNNING:
            raise PlaybackStreamError("Cannot write: playback is not running")

        loop = asyncio.get_running_loop()

        # Wrap blocking queue.put() in executor
        def blocking_put():
            self._queue.put(audio_data, block=True, timeout=timeout)

        if timeout:
            await asyncio.wait_for(
                loop.run_in_executor(None, blocking_put), timeout=timeout
            )
        else:
            await loop.run_in_executor(None, blocking_put)

    def write_chunk_nowait(self, audio_data: bytes) -> bool:
        """
        Write audio data to playback queue without blocking.

        Safe to call from any thread (including async code).

        Args:
            audio_data: Raw PCM audio bytes to play

        Returns:
            True if data was queued, False if queue was full
        """
        if self._state != PlaybackState.RUNNING:
            return False

        try:
            self._queue.put_nowait(audio_data)
            return True
        except queue.Full:
            logger.warning("Playback queue full, dropping chunk")
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


class SpeakerOutput(BasePlaybackDevice):
    """
    Plays audio through physical speakers.

    Optimized for playing translated speech from Gemini S2ST API:
    - 24kHz sample rate (Gemini API output format)
    - 16-bit PCM format
    - Mono channel
    - 1024 frame chunks for low latency

    Example:
        ```python
        async with SpeakerOutput() as speaker:
            while True:
                translated_audio = await get_from_gemini()
                await speaker.write_chunk(translated_audio)
        ```
    """

    def __init__(
        self,
        device_index: Optional[int] = None,
        sample_rate: int = SAMPLE_RATE_OUTPUT,
        chunk_size: int = CHUNK_SIZE,
    ):
        """
        Initialize speaker output.

        Args:
            device_index: PyAudio device index (None = default speakers)
            sample_rate: Sample rate in Hz (default: 24kHz for Gemini output)
            chunk_size: Buffer size in frames (default: 1024)
        """
        super().__init__(
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            channels=CHANNELS,
            device_index=device_index,
        )
        logger.info("SpeakerOutput initialized")


class VirtualMicOutput(BasePlaybackDevice):
    """
    Routes audio to a virtual microphone device.

    Used to send translated audio INTO Zoom calls via a virtual audio device
    (BlackHole on macOS, VB-Audio Cable on Windows).

    The virtual mic device must be:
    1. Installed on the system (BlackHole, VB-Audio, etc.)
    2. Selected as the input device in Zoom

    Example:
        ```python
        # Find BlackHole device index first
        device_idx = find_virtual_mic_device()

        async with VirtualMicOutput(device_index=device_idx.index) as virtual_mic:
            while True:
                translated_audio = await get_from_gemini()
                await virtual_mic.write_chunk(translated_audio)
        ```
    """

    def __init__(
        self,
        device_index: int,
        sample_rate: int = SAMPLE_RATE_OUTPUT,
        chunk_size: int = CHUNK_SIZE,
    ):
        """
        Initialize virtual microphone output.

        Args:
            device_index: PyAudio device index for virtual audio device (required)
            sample_rate: Sample rate in Hz (default: 24kHz)
            chunk_size: Buffer size in frames (default: 1024)
        """
        super().__init__(
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            channels=CHANNELS,
            device_index=device_index,
        )
        logger.info("VirtualMicOutput initialized")
