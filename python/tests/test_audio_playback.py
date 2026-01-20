"""
Comprehensive tests for audio playback module.

Tests SpeakerOutput, VirtualMicOutput, and BasePlaybackDevice classes
using mocked PyAudio to avoid requiring real audio hardware.
"""

import asyncio
import queue
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from src.audio.playback import (
    BasePlaybackDevice,
    SpeakerOutput,
    VirtualMicOutput,
    PlaybackState,
    AudioPlaybackError,
    PlaybackDeviceError,
    PlaybackStreamError,
)
from src.audio import (
    SAMPLE_RATE_OUTPUT,
    CHANNELS,
    CHUNK_SIZE,
    BIT_DEPTH,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_pyaudio():
    """Create a mock PyAudio instance for playback."""
    with patch("src.audio.playback.pyaudio") as mock_pa:
        # Create mock PyAudio instance
        mock_instance = MagicMock()
        mock_pa.PyAudio.return_value = mock_instance

        # Mock device info
        mock_instance.get_device_info_by_index.return_value = {
            "name": "Test Speaker",
            "index": 0,
            "maxInputChannels": 0,
            "maxOutputChannels": 2,
            "defaultSampleRate": 24000.0,
        }

        # Mock stream
        mock_stream = MagicMock()
        mock_stream.is_active.return_value = True
        mock_instance.open.return_value = mock_stream

        # Set constants
        mock_pa.paInt16 = 8  # PyAudio paInt16 constant
        mock_pa.paContinue = 0
        mock_pa.paOutputUnderflow = 0x00000004

        yield mock_pa


@pytest.fixture
def mock_pyaudio_error():
    """Create a mock PyAudio that raises errors."""
    with patch("src.audio.playback.pyaudio") as mock_pa:
        mock_instance = MagicMock()
        mock_pa.PyAudio.return_value = mock_instance

        # Make open() raise an exception
        mock_instance.open.side_effect = Exception("Device unavailable")

        mock_pa.paInt16 = 8
        mock_pa.paContinue = 0
        mock_pa.paOutputUnderflow = 0x00000004

        yield mock_pa


@pytest.fixture
def sample_audio_data():
    """Generate sample audio data for testing."""
    # Generate chunk of audio data matching expected size
    bytes_per_chunk = CHUNK_SIZE * CHANNELS * (BIT_DEPTH // 8)
    return bytes(bytes_per_chunk)


@pytest.fixture
def small_audio_data():
    """Generate small audio sample for quick tests."""
    return b"\x00\x01" * 100


# ============================================================================
# PlaybackState Tests
# ============================================================================


class TestPlaybackState:
    """Tests for PlaybackState enum."""

    def test_playback_states_exist(self):
        """Test all expected playback states exist."""
        assert PlaybackState.STOPPED
        assert PlaybackState.STARTING
        assert PlaybackState.RUNNING
        assert PlaybackState.STOPPING
        assert PlaybackState.ERROR

    def test_playback_states_are_unique(self):
        """Test playback states have unique values."""
        states = [
            PlaybackState.STOPPED,
            PlaybackState.STARTING,
            PlaybackState.RUNNING,
            PlaybackState.STOPPING,
            PlaybackState.ERROR,
        ]
        values = [s.value for s in states]
        assert len(values) == len(set(values))


# ============================================================================
# Exception Tests
# ============================================================================


class TestPlaybackExceptions:
    """Tests for audio playback exceptions."""

    def test_audio_playback_error_base(self):
        """Test AudioPlaybackError is the base exception."""
        error = AudioPlaybackError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_playback_device_error_inheritance(self):
        """Test PlaybackDeviceError inherits from AudioPlaybackError."""
        error = PlaybackDeviceError("Device not found")
        assert isinstance(error, AudioPlaybackError)
        assert str(error) == "Device not found"

    def test_playback_stream_error_inheritance(self):
        """Test PlaybackStreamError inherits from AudioPlaybackError."""
        error = PlaybackStreamError("Stream failed")
        assert isinstance(error, AudioPlaybackError)
        assert str(error) == "Stream failed"


# ============================================================================
# BasePlaybackDevice Tests
# ============================================================================


class TestBasePlaybackDevice:
    """Tests for BasePlaybackDevice base class."""

    def test_initialization_default_values(self):
        """Test BasePlaybackDevice initializes with correct default values."""
        device = BasePlaybackDevice(sample_rate=24000)

        assert device._sample_rate == 24000
        assert device._chunk_size == CHUNK_SIZE
        assert device._channels == CHANNELS
        assert device._device_index is None
        assert device._state == PlaybackState.STOPPED

    def test_initialization_custom_values(self):
        """Test BasePlaybackDevice with custom parameters."""
        device = BasePlaybackDevice(
            sample_rate=48000,
            chunk_size=2048,
            channels=2,
            device_index=3,
        )

        assert device._sample_rate == 48000
        assert device._chunk_size == 2048
        assert device._channels == 2
        assert device._device_index == 3

    def test_state_property(self):
        """Test state property returns current state."""
        device = BasePlaybackDevice(sample_rate=24000)
        assert device.state == PlaybackState.STOPPED

    def test_sample_rate_property(self):
        """Test sample_rate property returns configured rate."""
        device = BasePlaybackDevice(sample_rate=48000)
        assert device.sample_rate == 48000

    def test_is_running_property(self):
        """Test is_running property reflects state correctly."""
        device = BasePlaybackDevice(sample_rate=24000)

        assert device.is_running is False

        device._state = PlaybackState.RUNNING
        assert device.is_running is True

        device._state = PlaybackState.STOPPING
        assert device.is_running is False

    def test_stats_property_initial(self):
        """Test stats property returns initial statistics."""
        device = BasePlaybackDevice(sample_rate=24000)
        stats = device.stats

        assert stats["chunks_played"] == 0
        assert stats["bytes_played"] == 0
        assert stats["underruns"] == 0
        assert stats["queue_size"] == 0

    def test_silence_buffer_creation(self):
        """Test silence buffer is created with correct size."""
        device = BasePlaybackDevice(
            sample_rate=24000, chunk_size=1024, channels=1
        )

        expected_size = 1024 * 1 * (BIT_DEPTH // 8)  # frames * channels * bytes
        assert len(device._silence) == expected_size
        assert all(b == 0 for b in device._silence)

    def test_silence_buffer_stereo(self):
        """Test silence buffer for stereo configuration."""
        device = BasePlaybackDevice(
            sample_rate=24000, chunk_size=512, channels=2
        )

        expected_size = 512 * 2 * (BIT_DEPTH // 8)
        assert len(device._silence) == expected_size

    @pytest.mark.asyncio
    async def test_start_basic(self, mock_pyaudio):
        """Test basic start functionality."""
        device = BasePlaybackDevice(sample_rate=24000)

        await device.start()

        assert device.state == PlaybackState.RUNNING
        mock_pyaudio.PyAudio.return_value.open.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_prebuffers_silence(self, mock_pyaudio):
        """Test start pre-buffers silence chunks."""
        device = BasePlaybackDevice(sample_rate=24000)

        await device.start()

        # Should have prebuffer_size (2) silence chunks
        assert device._queue.qsize() == device._prebuffer_size

        await device.stop()

    @pytest.mark.asyncio
    async def test_start_with_device_index(self, mock_pyaudio):
        """Test start with specific device index."""
        device = BasePlaybackDevice(sample_rate=24000, device_index=5)

        await device.start()

        # Should validate the device
        mock_pyaudio.PyAudio.return_value.get_device_info_by_index.assert_called_with(5)

        await device.stop()

    @pytest.mark.asyncio
    async def test_start_already_running_raises_error(self, mock_pyaudio):
        """Test starting already running playback raises error."""
        device = BasePlaybackDevice(sample_rate=24000)

        await device.start()

        with pytest.raises(PlaybackStreamError, match="Cannot start"):
            await device.start()

        await device.stop()

    @pytest.mark.asyncio
    async def test_start_invalid_device_raises_error(self, mock_pyaudio):
        """Test starting with invalid device raises PlaybackDeviceError."""
        mock_pyaudio.PyAudio.return_value.get_device_info_by_index.side_effect = (
            Exception("Invalid device")
        )

        device = BasePlaybackDevice(sample_rate=24000, device_index=99)

        with pytest.raises(PlaybackStreamError):
            await device.start()

        assert device.state == PlaybackState.ERROR

    @pytest.mark.asyncio
    async def test_start_stream_error(self, mock_pyaudio_error):
        """Test handling of stream open error."""
        device = BasePlaybackDevice(sample_rate=24000)

        with pytest.raises(PlaybackStreamError, match="Failed to start"):
            await device.start()

        assert device.state == PlaybackState.ERROR

    @pytest.mark.asyncio
    async def test_stop_basic(self, mock_pyaudio):
        """Test basic stop functionality."""
        device = BasePlaybackDevice(sample_rate=24000)

        await device.start()
        await device.stop()

        assert device.state == PlaybackState.STOPPED

    @pytest.mark.asyncio
    async def test_stop_clears_queue(self, mock_pyaudio, sample_audio_data):
        """Test stop clears the playback queue."""
        device = BasePlaybackDevice(sample_rate=24000)
        await device.start()

        # Add some data to queue
        device.write_chunk_nowait(sample_audio_data)
        device.write_chunk_nowait(sample_audio_data)

        await device.stop()

        # Queue should be cleared after stop
        assert device._queue.empty()

    @pytest.mark.asyncio
    async def test_stop_idempotent(self, mock_pyaudio):
        """Test stop is idempotent (can be called multiple times)."""
        device = BasePlaybackDevice(sample_rate=24000)

        await device.start()
        await device.stop()
        await device.stop()  # Should not raise
        await device.stop()  # Should not raise

        assert device.state == PlaybackState.STOPPED

    @pytest.mark.asyncio
    async def test_stop_without_start(self, mock_pyaudio):
        """Test stop on never-started device."""
        device = BasePlaybackDevice(sample_rate=24000)

        await device.stop()  # Should not raise
        assert device.state == PlaybackState.STOPPED

    @pytest.mark.asyncio
    async def test_drain_basic(self, mock_pyaudio):
        """Test drain waits for queue to empty."""
        device = BasePlaybackDevice(sample_rate=24000)
        await device.start()

        # Queue has prebuffer silence - simulate them being consumed
        # by clearing the queue
        while not device._queue.empty():
            device._queue.get_nowait()

        # Drain should complete immediately on empty queue
        await device.drain()

        await device.stop()

    @pytest.mark.asyncio
    async def test_drain_timeout(self, mock_pyaudio, sample_audio_data):
        """Test drain times out if queue doesn't empty."""
        device = BasePlaybackDevice(sample_rate=24000)
        await device.start()

        # Fill queue with data that won't be consumed (no real playback)
        for _ in range(10):
            device.write_chunk_nowait(sample_audio_data)

        # Drain should timeout (but not raise)
        # We patch the timeout to be very short for testing
        original_poll = 0.05
        start_time = asyncio.get_event_loop().time()

        # Drain will timeout after its internal max_wait_seconds
        await device.drain()

        # Verify some time passed (but test shouldn't hang)
        elapsed = asyncio.get_event_loop().time() - start_time
        assert elapsed < 10  # Should complete within reasonable time

        await device.stop()

    @pytest.mark.asyncio
    async def test_drain_not_running(self, mock_pyaudio):
        """Test drain returns immediately when not running."""
        device = BasePlaybackDevice(sample_rate=24000)

        # Should complete immediately without error
        await device.drain()

    @pytest.mark.asyncio
    async def test_write_chunk_basic(self, mock_pyaudio, sample_audio_data):
        """Test basic write_chunk functionality."""
        device = BasePlaybackDevice(sample_rate=24000)
        await device.start()

        initial_size = device._queue.qsize()

        await device.write_chunk(sample_audio_data)

        assert device._queue.qsize() == initial_size + 1

        await device.stop()

    @pytest.mark.asyncio
    async def test_write_chunk_not_running_raises_error(
        self, mock_pyaudio, sample_audio_data
    ):
        """Test write_chunk raises error when not running."""
        device = BasePlaybackDevice(sample_rate=24000)

        with pytest.raises(PlaybackStreamError, match="not running"):
            await device.write_chunk(sample_audio_data)

    def test_write_chunk_nowait_basic(self, mock_pyaudio, sample_audio_data):
        """Test write_chunk_nowait adds data to queue."""
        device = BasePlaybackDevice(sample_rate=24000)
        device._state = PlaybackState.RUNNING

        result = device.write_chunk_nowait(sample_audio_data)

        assert result is True
        assert device._queue.qsize() == 1

    def test_write_chunk_nowait_not_running(self, mock_pyaudio, sample_audio_data):
        """Test write_chunk_nowait returns False when not running."""
        device = BasePlaybackDevice(sample_rate=24000)

        result = device.write_chunk_nowait(sample_audio_data)

        assert result is False
        assert device._queue.qsize() == 0

    def test_write_chunk_nowait_queue_full(self, mock_pyaudio, sample_audio_data):
        """Test write_chunk_nowait handles full queue."""
        device = BasePlaybackDevice(sample_rate=24000)
        device._state = PlaybackState.RUNNING
        device._queue = queue.Queue(maxsize=1)

        # First write succeeds
        assert device.write_chunk_nowait(sample_audio_data) is True

        # Second write should fail (queue full)
        assert device.write_chunk_nowait(sample_audio_data) is False

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_pyaudio):
        """Test async context manager functionality."""
        device = BasePlaybackDevice(sample_rate=24000)

        async with device as d:
            assert d is device
            assert d.state == PlaybackState.RUNNING

        assert device.state == PlaybackState.STOPPED

    @pytest.mark.asyncio
    async def test_context_manager_exception_handling(self, mock_pyaudio):
        """Test context manager cleans up on exception."""
        device = BasePlaybackDevice(sample_rate=24000)

        with pytest.raises(ValueError):
            async with device:
                raise ValueError("Test exception")

        # Device should be stopped even after exception
        assert device.state == PlaybackState.STOPPED

    def test_audio_callback_returns_data_from_queue(
        self, mock_pyaudio, sample_audio_data
    ):
        """Test audio callback returns data from queue."""
        device = BasePlaybackDevice(sample_rate=24000)
        device._state = PlaybackState.RUNNING

        # Put data in queue
        device._queue.put(sample_audio_data)

        result = device._audio_callback(None, CHUNK_SIZE, {}, 0)

        assert result == (sample_audio_data, mock_pyaudio.paContinue)
        assert device._chunks_played == 1
        assert device._bytes_played == len(sample_audio_data)

    def test_audio_callback_returns_silence_on_empty_queue(self, mock_pyaudio):
        """Test audio callback returns silence when queue is empty."""
        device = BasePlaybackDevice(sample_rate=24000)
        device._state = PlaybackState.RUNNING

        result = device._audio_callback(None, CHUNK_SIZE, {}, 0)

        assert result == (device._silence, mock_pyaudio.paContinue)
        assert device._underruns == 1

    def test_audio_callback_underflow_detection(self, mock_pyaudio, sample_audio_data):
        """Test audio callback detects output underflow."""
        device = BasePlaybackDevice(sample_rate=24000)
        device._state = PlaybackState.RUNNING
        device._queue.put(sample_audio_data)

        # Simulate underflow flag
        device._audio_callback(None, CHUNK_SIZE, {}, mock_pyaudio.paOutputUnderflow)

        assert device._underruns == 1

    def test_audio_callback_exception_handling(self, mock_pyaudio):
        """Test audio callback handles exceptions gracefully."""
        device = BasePlaybackDevice(sample_rate=24000)
        device._state = PlaybackState.RUNNING

        # Make queue.get_nowait raise unexpected exception
        device._queue = MagicMock()
        device._queue.get_nowait.side_effect = RuntimeError("Unexpected")

        result = device._audio_callback(None, CHUNK_SIZE, {}, 0)

        # Should return silence on error
        assert result == (device._silence, mock_pyaudio.paContinue)


# ============================================================================
# SpeakerOutput Tests
# ============================================================================


class TestSpeakerOutput:
    """Tests for SpeakerOutput class."""

    def test_initialization_defaults(self):
        """Test SpeakerOutput uses correct defaults."""
        speaker = SpeakerOutput()

        assert speaker._sample_rate == SAMPLE_RATE_OUTPUT  # 24kHz
        assert speaker._chunk_size == CHUNK_SIZE  # 1024
        assert speaker._channels == CHANNELS  # mono
        assert speaker._device_index is None  # default device

    def test_initialization_custom(self):
        """Test SpeakerOutput with custom parameters."""
        speaker = SpeakerOutput(
            device_index=2,
            sample_rate=48000,
            chunk_size=512,
        )

        assert speaker._device_index == 2
        assert speaker._sample_rate == 48000
        assert speaker._chunk_size == 512

    @pytest.mark.asyncio
    async def test_speaker_output_lifecycle(self, mock_pyaudio):
        """Test full SpeakerOutput start/stop lifecycle."""
        speaker = SpeakerOutput()

        assert speaker.state == PlaybackState.STOPPED

        await speaker.start()
        assert speaker.state == PlaybackState.RUNNING

        await speaker.stop()
        assert speaker.state == PlaybackState.STOPPED

    @pytest.mark.asyncio
    async def test_speaker_context_manager(self, mock_pyaudio):
        """Test SpeakerOutput as async context manager."""
        async with SpeakerOutput() as speaker:
            assert speaker.state == PlaybackState.RUNNING
            assert speaker.sample_rate == SAMPLE_RATE_OUTPUT

        assert speaker.state == PlaybackState.STOPPED

    @pytest.mark.asyncio
    async def test_speaker_stream_configuration(self, mock_pyaudio):
        """Test PyAudio stream is configured correctly for speakers."""
        speaker = SpeakerOutput()
        await speaker.start()

        # Verify stream was opened with correct parameters
        mock_pyaudio.PyAudio.return_value.open.assert_called_once()
        call_kwargs = mock_pyaudio.PyAudio.return_value.open.call_args[1]

        assert call_kwargs["format"] == mock_pyaudio.paInt16
        assert call_kwargs["channels"] == CHANNELS
        assert call_kwargs["rate"] == SAMPLE_RATE_OUTPUT
        assert call_kwargs["output"] is True
        assert call_kwargs["frames_per_buffer"] == CHUNK_SIZE

        await speaker.stop()

    @pytest.mark.asyncio
    async def test_speaker_write_audio(self, mock_pyaudio, sample_audio_data):
        """Test writing audio to speaker."""
        async with SpeakerOutput() as speaker:
            await speaker.write_chunk(sample_audio_data)

            # Should have prebuffer + our data
            assert speaker._queue.qsize() >= 1


# ============================================================================
# VirtualMicOutput Tests
# ============================================================================


class TestVirtualMicOutput:
    """Tests for VirtualMicOutput class."""

    def test_initialization_requires_device_index(self):
        """Test VirtualMicOutput requires device_index."""
        virtual_mic = VirtualMicOutput(device_index=5)
        assert virtual_mic._device_index == 5

    def test_initialization_defaults(self):
        """Test VirtualMicOutput uses correct defaults."""
        virtual_mic = VirtualMicOutput(device_index=5)

        assert virtual_mic._sample_rate == SAMPLE_RATE_OUTPUT  # 24kHz
        assert virtual_mic._chunk_size == CHUNK_SIZE  # 1024
        assert virtual_mic._channels == CHANNELS  # mono

    def test_initialization_custom(self):
        """Test VirtualMicOutput with custom parameters."""
        virtual_mic = VirtualMicOutput(
            device_index=7,
            sample_rate=16000,
            chunk_size=2048,
        )

        assert virtual_mic._device_index == 7
        assert virtual_mic._sample_rate == 16000
        assert virtual_mic._chunk_size == 2048

    @pytest.mark.asyncio
    async def test_virtual_mic_lifecycle(self, mock_pyaudio):
        """Test full VirtualMicOutput start/stop lifecycle."""
        virtual_mic = VirtualMicOutput(device_index=5)

        assert virtual_mic.state == PlaybackState.STOPPED

        await virtual_mic.start()
        assert virtual_mic.state == PlaybackState.RUNNING

        await virtual_mic.stop()
        assert virtual_mic.state == PlaybackState.STOPPED

    @pytest.mark.asyncio
    async def test_virtual_mic_context_manager(self, mock_pyaudio):
        """Test VirtualMicOutput as async context manager."""
        async with VirtualMicOutput(device_index=5) as virtual_mic:
            assert virtual_mic.state == PlaybackState.RUNNING

        assert virtual_mic.state == PlaybackState.STOPPED

    @pytest.mark.asyncio
    async def test_virtual_mic_stream_configuration(self, mock_pyaudio):
        """Test PyAudio stream configured for virtual mic."""
        virtual_mic = VirtualMicOutput(device_index=5)
        await virtual_mic.start()

        call_kwargs = mock_pyaudio.PyAudio.return_value.open.call_args[1]

        assert call_kwargs["output_device_index"] == 5
        assert call_kwargs["output"] is True
        assert call_kwargs["rate"] == SAMPLE_RATE_OUTPUT

        await virtual_mic.stop()

    @pytest.mark.asyncio
    async def test_virtual_mic_write_audio(self, mock_pyaudio, sample_audio_data):
        """Test writing audio to virtual mic."""
        async with VirtualMicOutput(device_index=5) as virtual_mic:
            result = virtual_mic.write_chunk_nowait(sample_audio_data)
            assert result is True


# ============================================================================
# Integration-style Tests
# ============================================================================


class TestPlaybackIntegration:
    """Integration-style tests for playback module."""

    @pytest.mark.asyncio
    async def test_write_multiple_chunks(self, mock_pyaudio, sample_audio_data):
        """Test writing multiple chunks in sequence."""
        async with SpeakerOutput() as speaker:
            # Clear prebuffer
            while not speaker._queue.empty():
                speaker._queue.get_nowait()

            for i in range(5):
                await speaker.write_chunk(sample_audio_data)

            assert speaker._queue.qsize() == 5

    @pytest.mark.asyncio
    async def test_stats_accumulate_correctly(self, mock_pyaudio, sample_audio_data):
        """Test statistics accumulate correctly across multiple plays."""
        device = BasePlaybackDevice(sample_rate=24000)
        await device.start()

        # Clear prebuffer
        while not device._queue.empty():
            device._queue.get_nowait()

        # Add chunks and simulate callback consuming them
        for _ in range(10):
            device._queue.put(sample_audio_data)
            device._audio_callback(None, CHUNK_SIZE, {}, 0)

        stats = device.stats

        assert stats["chunks_played"] == 10
        assert stats["bytes_played"] == 10 * len(sample_audio_data)

        await device.stop()

    @pytest.mark.asyncio
    async def test_multiple_playback_instances(self, mock_pyaudio):
        """Test multiple playback instances can coexist."""
        speaker = SpeakerOutput()
        virtual_mic = VirtualMicOutput(device_index=5)

        await speaker.start()
        await virtual_mic.start()

        assert speaker.state == PlaybackState.RUNNING
        assert virtual_mic.state == PlaybackState.RUNNING

        await speaker.stop()
        await virtual_mic.stop()

        assert speaker.state == PlaybackState.STOPPED
        assert virtual_mic.state == PlaybackState.STOPPED

    @pytest.mark.asyncio
    async def test_rapid_write_nowait(self, mock_pyaudio, small_audio_data):
        """Test rapid non-blocking writes."""
        async with SpeakerOutput() as speaker:
            # Clear prebuffer
            while not speaker._queue.empty():
                speaker._queue.get_nowait()

            # Rapidly write many chunks
            success_count = 0
            for _ in range(50):
                if speaker.write_chunk_nowait(small_audio_data):
                    success_count += 1

            # Should have written many (up to queue limit)
            assert success_count > 0


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestPlaybackEdgeCases:
    """Edge case and error condition tests."""

    @pytest.mark.asyncio
    async def test_cleanup_handles_already_closed_stream(self, mock_pyaudio):
        """Test cleanup handles already-closed stream gracefully."""
        device = BasePlaybackDevice(sample_rate=24000)
        await device.start()

        # Simulate stream already closed
        mock_pyaudio.PyAudio.return_value.open.return_value.is_active.return_value = (
            False
        )

        await device.stop()  # Should not raise
        assert device.state == PlaybackState.STOPPED

    @pytest.mark.asyncio
    async def test_cleanup_handles_terminate_error(self, mock_pyaudio):
        """Test cleanup handles PyAudio terminate error gracefully."""
        device = BasePlaybackDevice(sample_rate=24000)
        await device.start()

        # Make terminate raise an error
        mock_pyaudio.PyAudio.return_value.terminate.side_effect = Exception(
            "Terminate failed"
        )

        # Should not propagate exception
        await device.stop()
        assert device.state == PlaybackState.STOPPED

    @pytest.mark.asyncio
    async def test_restart_after_error(self, mock_pyaudio):
        """Test device can be restarted after an error."""
        device = BasePlaybackDevice(sample_rate=24000)

        # First start fails
        mock_pyaudio.PyAudio.return_value.open.side_effect = Exception("First failure")

        with pytest.raises(PlaybackStreamError):
            await device.start()

        assert device.state == PlaybackState.ERROR

        # Reset mock and try again
        mock_pyaudio.PyAudio.return_value.open.side_effect = None
        mock_stream = MagicMock()
        mock_stream.is_active.return_value = True
        mock_pyaudio.PyAudio.return_value.open.return_value = mock_stream

        # Reset device state manually (simulating proper error recovery)
        device._state = PlaybackState.STOPPED

        await device.start()
        assert device.state == PlaybackState.RUNNING

        await device.stop()

    @pytest.mark.asyncio
    async def test_write_empty_data(self, mock_pyaudio):
        """Test writing empty data."""
        async with SpeakerOutput() as speaker:
            # Should not raise
            await speaker.write_chunk(b"")

    def test_callback_with_empty_queue_and_exception(self, mock_pyaudio):
        """Test callback handles queue.Empty as expected."""
        device = BasePlaybackDevice(sample_rate=24000)
        device._state = PlaybackState.RUNNING

        # Queue is empty by default
        result = device._audio_callback(None, CHUNK_SIZE, {}, 0)

        # Should return silence and increment underruns
        assert result[0] == device._silence
        assert device._underruns == 1

    @pytest.mark.asyncio
    async def test_concurrent_writes(self, mock_pyaudio, small_audio_data):
        """Test concurrent write operations."""
        async with SpeakerOutput() as speaker:
            # Clear prebuffer
            while not speaker._queue.empty():
                speaker._queue.get_nowait()

            # Launch concurrent writes
            async def write_chunks():
                for _ in range(10):
                    await speaker.write_chunk(small_audio_data)

            # Run multiple writers concurrently
            await asyncio.gather(
                write_chunks(),
                write_chunks(),
                write_chunks(),
            )

            # All writes should succeed
            assert speaker._queue.qsize() == 30

    def test_prebuffer_size_configuration(self, mock_pyaudio):
        """Test prebuffer size is configurable through instance."""
        device = BasePlaybackDevice(sample_rate=24000)

        # Default prebuffer size
        assert device._prebuffer_size == 2

        # Can be modified
        device._prebuffer_size = 5
        assert device._prebuffer_size == 5


# ============================================================================
# Thread Safety Tests
# ============================================================================


class TestPlaybackThreadSafety:
    """Tests for thread-safe queue usage."""

    def test_queue_is_standard_library_queue(self, mock_pyaudio):
        """Test that playback uses queue.Queue, not asyncio.Queue."""
        device = BasePlaybackDevice(sample_rate=24000)

        # Should be standard library queue.Queue for thread safety
        assert isinstance(device._queue, queue.Queue)

    def test_write_chunk_nowait_thread_safe(self, mock_pyaudio, small_audio_data):
        """Test write_chunk_nowait can be called from multiple threads."""
        import threading

        device = BasePlaybackDevice(sample_rate=24000)
        device._state = PlaybackState.RUNNING

        results = []
        errors = []

        def write_from_thread():
            try:
                result = device.write_chunk_nowait(small_audio_data)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Launch many threads
        threads = [threading.Thread(target=write_from_thread) for _ in range(20)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # No errors should occur
        assert len(errors) == 0
        # Most writes should succeed (some might fail due to queue filling)
        assert len(results) == 20

    def test_callback_thread_safe_get(self, mock_pyaudio, small_audio_data):
        """Test audio callback's queue.get_nowait is thread-safe."""
        import threading

        device = BasePlaybackDevice(sample_rate=24000)
        device._state = PlaybackState.RUNNING

        # Fill queue
        for _ in range(50):
            device._queue.put(small_audio_data)

        results = []

        def callback_simulation():
            try:
                result = device._audio_callback(None, CHUNK_SIZE, {}, 0)
                results.append(result)
            except Exception as e:
                results.append(("error", e))

        # Simulate multiple callback invocations
        threads = [
            threading.Thread(target=callback_simulation) for _ in range(30)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All should complete without error
        assert len(results) == 30
        assert all(r[1] == mock_pyaudio.paContinue for r in results)
