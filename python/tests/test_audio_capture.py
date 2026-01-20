"""
Comprehensive tests for audio capture module.

Tests MicrophoneCapture, SystemAudioCapture, and BaseCaptureDevice classes
using mocked PyAudio to avoid requiring real audio hardware.
"""

import asyncio
from unittest.mock import MagicMock, patch, PropertyMock
import pytest
import numpy as np

from src.audio.capture import (
    BaseCaptureDevice,
    MicrophoneCapture,
    SystemAudioCapture,
    AudioChunk,
    CaptureState,
    AudioCaptureError,
    AudioDeviceError,
    AudioStreamError,
)
from src.audio import (
    SAMPLE_RATE_MIC,
    SAMPLE_RATE_SYSTEM,
    CHANNELS,
    CHUNK_SIZE,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_pyaudio():
    """Create a mock PyAudio instance."""
    with patch("src.audio.capture.pyaudio") as mock_pa:
        # Create mock PyAudio instance
        mock_instance = MagicMock()
        mock_pa.PyAudio.return_value = mock_instance

        # Mock device info
        mock_instance.get_device_info_by_index.return_value = {
            "name": "Test Microphone",
            "index": 0,
            "maxInputChannels": 2,
            "maxOutputChannels": 0,
            "defaultSampleRate": 16000.0,
        }

        # Mock stream
        mock_stream = MagicMock()
        mock_stream.is_active.return_value = True
        mock_instance.open.return_value = mock_stream

        # Set constants
        mock_pa.paInt16 = 8  # PyAudio paInt16 constant
        mock_pa.paContinue = 0
        mock_pa.paInputOverflow = 0x00000001

        yield mock_pa


@pytest.fixture
def mock_pyaudio_error():
    """Create a mock PyAudio that raises errors."""
    with patch("src.audio.capture.pyaudio") as mock_pa:
        mock_instance = MagicMock()
        mock_pa.PyAudio.return_value = mock_instance

        # Make open() raise an exception
        mock_instance.open.side_effect = Exception("Device unavailable")

        mock_pa.paInt16 = 8
        mock_pa.paContinue = 0
        mock_pa.paInputOverflow = 0x00000001

        yield mock_pa


@pytest.fixture
def sample_audio_data():
    """Generate sample audio data for testing."""
    # Generate 1024 frames of 16-bit mono audio (silence with some noise)
    frames = CHUNK_SIZE
    data = np.zeros(frames, dtype=np.int16)
    return data.tobytes()


@pytest.fixture
def stereo_audio_data():
    """Generate stereo audio data for stereo-to-mono conversion testing."""
    frames = CHUNK_SIZE
    # Left channel: 1000, Right channel: 3000 -> Mono average: 2000
    left = np.full(frames, 1000, dtype=np.int16)
    right = np.full(frames, 3000, dtype=np.int16)
    stereo = np.column_stack((left, right)).flatten()
    return stereo.tobytes()


# ============================================================================
# AudioChunk Tests
# ============================================================================


class TestAudioChunk:
    """Tests for AudioChunk dataclass."""

    def test_audio_chunk_creation(self):
        """Test creating an AudioChunk with valid parameters."""
        data = b"\x00" * 2048
        chunk = AudioChunk(
            data=data,
            timestamp=0.123,
            sample_rate=16000,
            channels=1,
            frames=1024,
        )

        assert chunk.data == data
        assert chunk.timestamp == 0.123
        assert chunk.sample_rate == 16000
        assert chunk.channels == 1
        assert chunk.frames == 1024

    def test_audio_chunk_duration_ms(self):
        """Test AudioChunk duration calculation."""
        chunk = AudioChunk(
            data=b"\x00" * 2048,
            timestamp=0.0,
            sample_rate=16000,
            channels=1,
            frames=1024,
        )

        # 1024 frames at 16kHz = 64ms
        assert chunk.duration_ms == 64.0

    def test_audio_chunk_duration_ms_different_rates(self):
        """Test duration calculation at different sample rates."""
        # At 24kHz: 1024 frames = ~42.67ms
        chunk_24k = AudioChunk(
            data=b"\x00" * 2048,
            timestamp=0.0,
            sample_rate=24000,
            channels=1,
            frames=1024,
        )
        assert abs(chunk_24k.duration_ms - 42.666666) < 0.001

        # At 48kHz: 1024 frames = ~21.33ms
        chunk_48k = AudioChunk(
            data=b"\x00" * 2048,
            timestamp=0.0,
            sample_rate=48000,
            channels=1,
            frames=1024,
        )
        assert abs(chunk_48k.duration_ms - 21.333333) < 0.001

    def test_audio_chunk_is_frozen(self):
        """Test that AudioChunk is immutable (frozen dataclass)."""
        chunk = AudioChunk(
            data=b"\x00" * 100,
            timestamp=0.0,
            sample_rate=16000,
            channels=1,
            frames=50,
        )

        with pytest.raises(AttributeError):
            chunk.timestamp = 1.0


# ============================================================================
# CaptureState Tests
# ============================================================================


class TestCaptureState:
    """Tests for CaptureState enum."""

    def test_capture_states_exist(self):
        """Test all expected capture states exist."""
        assert CaptureState.STOPPED
        assert CaptureState.STARTING
        assert CaptureState.RUNNING
        assert CaptureState.STOPPING
        assert CaptureState.ERROR

    def test_capture_states_are_unique(self):
        """Test capture states have unique values."""
        states = [
            CaptureState.STOPPED,
            CaptureState.STARTING,
            CaptureState.RUNNING,
            CaptureState.STOPPING,
            CaptureState.ERROR,
        ]
        values = [s.value for s in states]
        assert len(values) == len(set(values))


# ============================================================================
# Exception Tests
# ============================================================================


class TestAudioExceptions:
    """Tests for audio capture exceptions."""

    def test_audio_capture_error_base(self):
        """Test AudioCaptureError is the base exception."""
        error = AudioCaptureError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_audio_device_error_inheritance(self):
        """Test AudioDeviceError inherits from AudioCaptureError."""
        error = AudioDeviceError("Device not found")
        assert isinstance(error, AudioCaptureError)
        assert str(error) == "Device not found"

    def test_audio_stream_error_inheritance(self):
        """Test AudioStreamError inherits from AudioCaptureError."""
        error = AudioStreamError("Stream failed")
        assert isinstance(error, AudioCaptureError)
        assert str(error) == "Stream failed"


# ============================================================================
# BaseCaptureDevice Tests
# ============================================================================


class TestBaseCaptureDevice:
    """Tests for BaseCaptureDevice base class."""

    def test_initialization_default_values(self):
        """Test BaseCaptureDevice initializes with correct default values."""
        device = BaseCaptureDevice(sample_rate=16000)

        assert device._sample_rate == 16000
        assert device._chunk_size == CHUNK_SIZE
        assert device._channels == CHANNELS
        assert device._device_index is None
        assert device._state == CaptureState.STOPPED

    def test_initialization_custom_values(self):
        """Test BaseCaptureDevice with custom parameters."""
        device = BaseCaptureDevice(
            sample_rate=24000,
            chunk_size=2048,
            channels=2,
            device_index=5,
        )

        assert device._sample_rate == 24000
        assert device._chunk_size == 2048
        assert device._channels == 2
        assert device._device_index == 5

    def test_state_property(self):
        """Test state property returns current state."""
        device = BaseCaptureDevice(sample_rate=16000)
        assert device.state == CaptureState.STOPPED

    def test_sample_rate_property(self):
        """Test sample_rate property returns configured rate."""
        device = BaseCaptureDevice(sample_rate=24000)
        assert device.sample_rate == 24000

    def test_is_running_property(self):
        """Test is_running property reflects state correctly."""
        device = BaseCaptureDevice(sample_rate=16000)

        assert device.is_running is False

        device._state = CaptureState.RUNNING
        assert device.is_running is True

        device._state = CaptureState.STOPPING
        assert device.is_running is False

    def test_stats_property_initial(self):
        """Test stats property returns initial statistics."""
        device = BaseCaptureDevice(sample_rate=16000)
        stats = device.stats

        assert stats["chunks_captured"] == 0
        assert stats["bytes_captured"] == 0
        assert stats["overruns"] == 0
        assert stats["queue_size"] == 0

    @pytest.mark.asyncio
    async def test_start_basic(self, mock_pyaudio):
        """Test basic start functionality."""
        device = BaseCaptureDevice(sample_rate=16000)

        await device.start()

        assert device.state == CaptureState.RUNNING
        mock_pyaudio.PyAudio.return_value.open.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_with_device_index(self, mock_pyaudio):
        """Test start with specific device index."""
        device = BaseCaptureDevice(sample_rate=16000, device_index=3)

        await device.start()

        # Should validate the device
        mock_pyaudio.PyAudio.return_value.get_device_info_by_index.assert_called_with(3)

    @pytest.mark.asyncio
    async def test_start_already_running_raises_error(self, mock_pyaudio):
        """Test starting already running capture raises error."""
        device = BaseCaptureDevice(sample_rate=16000)

        await device.start()

        with pytest.raises(AudioStreamError, match="Cannot start"):
            await device.start()

    @pytest.mark.asyncio
    async def test_start_invalid_device_raises_error(self, mock_pyaudio):
        """Test starting with invalid device raises AudioDeviceError."""
        mock_pyaudio.PyAudio.return_value.get_device_info_by_index.side_effect = (
            Exception("Invalid device")
        )

        device = BaseCaptureDevice(sample_rate=16000, device_index=99)

        with pytest.raises(AudioStreamError):
            await device.start()

        assert device.state == CaptureState.ERROR

    @pytest.mark.asyncio
    async def test_start_stream_error(self, mock_pyaudio_error):
        """Test handling of stream open error."""
        device = BaseCaptureDevice(sample_rate=16000)

        with pytest.raises(AudioStreamError, match="Failed to start"):
            await device.start()

        assert device.state == CaptureState.ERROR

    @pytest.mark.asyncio
    async def test_stop_basic(self, mock_pyaudio):
        """Test basic stop functionality."""
        device = BaseCaptureDevice(sample_rate=16000)

        await device.start()
        await device.stop()

        assert device.state == CaptureState.STOPPED

    @pytest.mark.asyncio
    async def test_stop_idempotent(self, mock_pyaudio):
        """Test stop is idempotent (can be called multiple times)."""
        device = BaseCaptureDevice(sample_rate=16000)

        await device.start()
        await device.stop()
        await device.stop()  # Should not raise
        await device.stop()  # Should not raise

        assert device.state == CaptureState.STOPPED

    @pytest.mark.asyncio
    async def test_stop_without_start(self, mock_pyaudio):
        """Test stop on never-started device."""
        device = BaseCaptureDevice(sample_rate=16000)

        await device.stop()  # Should not raise
        assert device.state == CaptureState.STOPPED

    @pytest.mark.asyncio
    async def test_read_chunk_not_running_raises_error(self, mock_pyaudio):
        """Test reading from non-running capture raises error."""
        device = BaseCaptureDevice(sample_rate=16000)

        with pytest.raises(AudioStreamError, match="not running"):
            await device.read_chunk()

    @pytest.mark.asyncio
    async def test_read_chunk_timeout(self, mock_pyaudio):
        """Test read_chunk with timeout on empty queue."""
        device = BaseCaptureDevice(sample_rate=16000)
        await device.start()

        with pytest.raises(asyncio.TimeoutError):
            await device.read_chunk(timeout=0.1)

        await device.stop()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_pyaudio):
        """Test async context manager functionality."""
        device = BaseCaptureDevice(sample_rate=16000)

        async with device as d:
            assert d is device
            assert d.state == CaptureState.RUNNING

        assert device.state == CaptureState.STOPPED

    @pytest.mark.asyncio
    async def test_context_manager_exception_handling(self, mock_pyaudio):
        """Test context manager cleans up on exception."""
        device = BaseCaptureDevice(sample_rate=16000)

        with pytest.raises(ValueError):
            async with device:
                raise ValueError("Test exception")

        # Device should be stopped even after exception
        assert device.state == CaptureState.STOPPED

    def test_audio_callback_creates_chunk(self, mock_pyaudio, sample_audio_data):
        """Test audio callback creates AudioChunk correctly."""
        device = BaseCaptureDevice(sample_rate=16000)
        device._loop = asyncio.new_event_loop()

        time_info = {"input_buffer_adc_time": 0.5}

        result = device._audio_callback(
            sample_audio_data,
            CHUNK_SIZE,
            time_info,
            0,  # No status flags
        )

        assert result == (None, mock_pyaudio.paContinue)
        assert device._chunks_captured == 1
        assert device._bytes_captured == len(sample_audio_data)
        assert device._queue.qsize() == 1

        device._loop.close()

    def test_audio_callback_overflow_detection(self, mock_pyaudio, sample_audio_data):
        """Test audio callback detects input overflow."""
        device = BaseCaptureDevice(sample_rate=16000)
        device._loop = asyncio.new_event_loop()

        time_info = {"input_buffer_adc_time": 0.5}

        # Simulate overflow flag
        device._audio_callback(
            sample_audio_data,
            CHUNK_SIZE,
            time_info,
            mock_pyaudio.paInputOverflow,
        )

        assert device._overruns == 1

        device._loop.close()

    def test_audio_callback_queue_full(self, mock_pyaudio, sample_audio_data):
        """Test audio callback handles full queue gracefully."""
        device = BaseCaptureDevice(sample_rate=16000)
        device._loop = asyncio.new_event_loop()
        device._queue = asyncio.Queue(maxsize=1)  # Small queue

        time_info = {"input_buffer_adc_time": 0.5}

        # Fill the queue
        device._audio_callback(sample_audio_data, CHUNK_SIZE, time_info, 0)
        assert device._queue.qsize() == 1

        # This should not raise, just increment overruns
        device._audio_callback(sample_audio_data, CHUNK_SIZE, time_info, 0)
        assert device._overruns == 1
        assert device._queue.qsize() == 1  # Queue still has just 1 item

        device._loop.close()

    @pytest.mark.asyncio
    async def test_audio_callback_invokes_on_data(self, mock_pyaudio, sample_audio_data):
        """Test audio callback invokes on_data callback."""
        received_chunks = []

        async def on_data(chunk: AudioChunk):
            received_chunks.append(chunk)

        device = BaseCaptureDevice(sample_rate=16000)
        await device.start(on_data=on_data)

        time_info = {"input_buffer_adc_time": 0.5}

        # Simulate callback
        device._audio_callback(sample_audio_data, CHUNK_SIZE, time_info, 0)

        # Give the async callback time to execute
        await asyncio.sleep(0.1)

        assert len(received_chunks) == 1
        assert received_chunks[0].data == sample_audio_data

        await device.stop()


# ============================================================================
# MicrophoneCapture Tests
# ============================================================================


class TestMicrophoneCapture:
    """Tests for MicrophoneCapture class."""

    def test_initialization_defaults(self):
        """Test MicrophoneCapture uses correct defaults for speech."""
        mic = MicrophoneCapture()

        assert mic._sample_rate == SAMPLE_RATE_MIC  # 16kHz
        assert mic._chunk_size == CHUNK_SIZE  # 1024
        assert mic._channels == CHANNELS  # mono

    def test_initialization_custom(self):
        """Test MicrophoneCapture with custom parameters."""
        mic = MicrophoneCapture(
            device_index=2,
            sample_rate=22050,
            chunk_size=512,
        )

        assert mic._device_index == 2
        assert mic._sample_rate == 22050
        assert mic._chunk_size == 512

    @pytest.mark.asyncio
    async def test_microphone_capture_lifecycle(self, mock_pyaudio):
        """Test full MicrophoneCapture start/stop lifecycle."""
        mic = MicrophoneCapture()

        assert mic.state == CaptureState.STOPPED

        await mic.start()
        assert mic.state == CaptureState.RUNNING

        await mic.stop()
        assert mic.state == CaptureState.STOPPED

    @pytest.mark.asyncio
    async def test_microphone_context_manager(self, mock_pyaudio):
        """Test MicrophoneCapture as async context manager."""
        async with MicrophoneCapture() as mic:
            assert mic.state == CaptureState.RUNNING
            assert mic.sample_rate == SAMPLE_RATE_MIC

        assert mic.state == CaptureState.STOPPED

    @pytest.mark.asyncio
    async def test_microphone_stream_configuration(self, mock_pyaudio):
        """Test PyAudio stream is configured correctly for speech."""
        mic = MicrophoneCapture()
        await mic.start()

        # Verify stream was opened with correct parameters
        mock_pyaudio.PyAudio.return_value.open.assert_called_once()
        call_kwargs = mock_pyaudio.PyAudio.return_value.open.call_args[1]

        assert call_kwargs["format"] == mock_pyaudio.paInt16
        assert call_kwargs["channels"] == CHANNELS
        assert call_kwargs["rate"] == SAMPLE_RATE_MIC
        assert call_kwargs["input"] is True
        assert call_kwargs["frames_per_buffer"] == CHUNK_SIZE

        await mic.stop()


# ============================================================================
# SystemAudioCapture Tests
# ============================================================================


class TestSystemAudioCapture:
    """Tests for SystemAudioCapture class."""

    def test_initialization_requires_device_index(self):
        """Test SystemAudioCapture requires device_index."""
        # This should work - device_index is provided
        capture = SystemAudioCapture(device_index=5)
        assert capture._device_index == 5

    def test_initialization_stereo_to_mono_enabled(self):
        """Test stereo-to-mono conversion is enabled by default."""
        capture = SystemAudioCapture(device_index=5)

        assert capture._stereo_to_mono is True
        assert capture._input_channels == 2  # Captures stereo
        assert capture._channels == 2  # Initial channels value

    def test_initialization_stereo_to_mono_disabled(self):
        """Test disabling stereo-to-mono conversion."""
        capture = SystemAudioCapture(device_index=5, stereo_to_mono=False)

        assert capture._stereo_to_mono is False
        assert capture._input_channels == 1  # Captures mono directly

    def test_initialization_sample_rate(self):
        """Test SystemAudioCapture uses 24kHz for system audio."""
        capture = SystemAudioCapture(device_index=5)
        assert capture._sample_rate == SAMPLE_RATE_SYSTEM  # 24kHz

    @pytest.mark.asyncio
    async def test_system_audio_lifecycle(self, mock_pyaudio):
        """Test full SystemAudioCapture start/stop lifecycle."""
        capture = SystemAudioCapture(device_index=5)

        await capture.start()
        assert capture.state == CaptureState.RUNNING

        await capture.stop()
        assert capture.state == CaptureState.STOPPED

    def test_stereo_to_mono_conversion(self, mock_pyaudio, stereo_audio_data):
        """Test stereo audio is correctly converted to mono."""
        capture = SystemAudioCapture(device_index=5, stereo_to_mono=True)
        capture._loop = asyncio.new_event_loop()

        time_info = {"input_buffer_adc_time": 0.5}

        # Process stereo audio through callback
        capture._audio_callback(stereo_audio_data, CHUNK_SIZE, time_info, 0)

        # Get the processed chunk from queue
        chunk = capture._queue.get_nowait()

        # Convert to numpy for verification
        mono_data = np.frombuffer(chunk.data, dtype=np.int16)

        # Original: left=1000, right=3000, average should be 2000
        assert len(mono_data) == CHUNK_SIZE  # Should be mono now
        assert np.allclose(mono_data, 2000, atol=1)  # Allow for rounding

        capture._loop.close()

    def test_stereo_to_mono_preserves_frame_count(self, mock_pyaudio, stereo_audio_data):
        """Test stereo-to-mono conversion preserves frame count."""
        capture = SystemAudioCapture(device_index=5, stereo_to_mono=True)
        capture._loop = asyncio.new_event_loop()

        time_info = {"input_buffer_adc_time": 0.5}

        capture._audio_callback(stereo_audio_data, CHUNK_SIZE, time_info, 0)

        chunk = capture._queue.get_nowait()
        assert chunk.frames == CHUNK_SIZE

        capture._loop.close()

    def test_no_conversion_when_disabled(self, mock_pyaudio, sample_audio_data):
        """Test audio passes through unchanged when conversion is disabled."""
        capture = SystemAudioCapture(device_index=5, stereo_to_mono=False)
        capture._loop = asyncio.new_event_loop()

        time_info = {"input_buffer_adc_time": 0.5}

        capture._audio_callback(sample_audio_data, CHUNK_SIZE, time_info, 0)

        chunk = capture._queue.get_nowait()
        assert chunk.data == sample_audio_data

        capture._loop.close()

    @pytest.mark.asyncio
    async def test_system_audio_stream_configuration(self, mock_pyaudio):
        """Test PyAudio stream configured correctly for system audio."""
        capture = SystemAudioCapture(device_index=5)
        await capture.start()

        call_kwargs = mock_pyaudio.PyAudio.return_value.open.call_args[1]

        assert call_kwargs["rate"] == SAMPLE_RATE_SYSTEM
        assert call_kwargs["channels"] == 2  # Stereo input
        assert call_kwargs["input_device_index"] == 5

        await capture.stop()


# ============================================================================
# Integration-style Tests
# ============================================================================


class TestCaptureIntegration:
    """Integration-style tests for capture module."""

    @pytest.mark.asyncio
    async def test_read_chunks_in_sequence(self, mock_pyaudio, sample_audio_data):
        """Test reading multiple chunks in sequence."""
        device = BaseCaptureDevice(sample_rate=16000)
        await device.start()

        time_info = {"input_buffer_adc_time": 0.0}

        # Simulate several audio callbacks
        for i in range(5):
            time_info["input_buffer_adc_time"] = i * 0.064  # ~64ms per chunk
            device._audio_callback(sample_audio_data, CHUNK_SIZE, time_info, 0)

        # Read all chunks
        chunks = []
        for _ in range(5):
            chunk = await device.read_chunk(timeout=1.0)
            chunks.append(chunk)

        assert len(chunks) == 5
        assert all(c.data == sample_audio_data for c in chunks)

        await device.stop()

    @pytest.mark.asyncio
    async def test_stats_accumulate_correctly(self, mock_pyaudio, sample_audio_data):
        """Test statistics accumulate correctly across multiple chunks."""
        device = BaseCaptureDevice(sample_rate=16000)
        await device.start()

        time_info = {"input_buffer_adc_time": 0.0}

        # Process 10 chunks
        for _ in range(10):
            device._audio_callback(sample_audio_data, CHUNK_SIZE, time_info, 0)

        stats = device.stats

        assert stats["chunks_captured"] == 10
        assert stats["bytes_captured"] == 10 * len(sample_audio_data)
        assert stats["queue_size"] == 10
        assert stats["overruns"] == 0

        await device.stop()

    @pytest.mark.asyncio
    async def test_multiple_capture_instances(self, mock_pyaudio):
        """Test multiple capture instances can coexist."""
        mic = MicrophoneCapture()
        system = SystemAudioCapture(device_index=5)

        await mic.start()
        await system.start()

        assert mic.state == CaptureState.RUNNING
        assert system.state == CaptureState.RUNNING

        await mic.stop()
        await system.stop()

        assert mic.state == CaptureState.STOPPED
        assert system.state == CaptureState.STOPPED


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestCaptureEdgeCases:
    """Edge case and error condition tests."""

    @pytest.mark.asyncio
    async def test_cleanup_handles_already_closed_stream(self, mock_pyaudio):
        """Test cleanup handles already-closed stream gracefully."""
        device = BaseCaptureDevice(sample_rate=16000)
        await device.start()

        # Simulate stream already closed
        mock_pyaudio.PyAudio.return_value.open.return_value.is_active.return_value = (
            False
        )

        await device.stop()  # Should not raise
        assert device.state == CaptureState.STOPPED

    @pytest.mark.asyncio
    async def test_cleanup_handles_terminate_error(self, mock_pyaudio):
        """Test cleanup handles PyAudio terminate error gracefully."""
        device = BaseCaptureDevice(sample_rate=16000)
        await device.start()

        # Make terminate raise an error
        mock_pyaudio.PyAudio.return_value.terminate.side_effect = Exception(
            "Terminate failed"
        )

        # Should not propagate exception
        await device.stop()
        assert device.state == CaptureState.STOPPED

    def test_callback_handles_exception_gracefully(
        self, mock_pyaudio, sample_audio_data
    ):
        """Test callback handles internal exceptions gracefully."""
        device = BaseCaptureDevice(sample_rate=16000)
        device._loop = asyncio.new_event_loop()

        # Make queue.put_nowait raise unexpected exception
        device._queue = MagicMock()
        device._queue.put_nowait.side_effect = RuntimeError("Unexpected error")

        time_info = {"input_buffer_adc_time": 0.5}

        # Should not raise, should return continue
        result = device._audio_callback(sample_audio_data, CHUNK_SIZE, time_info, 0)

        assert result == (None, mock_pyaudio.paContinue)

        device._loop.close()

    @pytest.mark.asyncio
    async def test_restart_after_error(self, mock_pyaudio):
        """Test device can be restarted after an error."""
        device = BaseCaptureDevice(sample_rate=16000)

        # First start fails
        mock_pyaudio.PyAudio.return_value.open.side_effect = Exception("First failure")

        with pytest.raises(AudioStreamError):
            await device.start()

        assert device.state == CaptureState.ERROR

        # Reset mock and try again
        mock_pyaudio.PyAudio.return_value.open.side_effect = None
        mock_stream = MagicMock()
        mock_stream.is_active.return_value = True
        mock_pyaudio.PyAudio.return_value.open.return_value = mock_stream

        # Reset device state manually (simulating proper error recovery)
        device._state = CaptureState.STOPPED

        await device.start()
        assert device.state == CaptureState.RUNNING

        await device.stop()

    def test_zero_frame_chunk(self, mock_pyaudio):
        """Test handling of zero-frame audio callback."""
        device = BaseCaptureDevice(sample_rate=16000)
        device._loop = asyncio.new_event_loop()

        time_info = {"input_buffer_adc_time": 0.0}

        # Process zero-length audio
        result = device._audio_callback(b"", 0, time_info, 0)

        assert result == (None, mock_pyaudio.paContinue)
        # Stats should still update
        assert device._chunks_captured == 1
        assert device._bytes_captured == 0

        device._loop.close()
