"""
Comprehensive tests for audio device enumeration module.

Tests AudioDeviceManager, AudioDevice dataclass, and helper functions
using mocked PyAudio to avoid requiring real audio hardware.
"""

from unittest.mock import MagicMock, patch
import pytest

from src.audio.devices import (
    AudioDevice,
    AudioDeviceManager,
    DeviceType,
    list_audio_devices,
    find_microphone_device,
    find_loopback_device,
    find_speaker_device,
    find_virtual_mic_device,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_pyaudio():
    """Create a mock PyAudio instance with sample devices."""
    with patch("src.audio.devices.pyaudio") as mock_pa:
        mock_instance = MagicMock()
        mock_pa.PyAudio.return_value = mock_instance

        # Define sample devices
        devices = [
            {
                "name": "Built-in Microphone",
                "index": 0,
                "hostApi": 0,
                "maxInputChannels": 2,
                "maxOutputChannels": 0,
                "defaultSampleRate": 44100.0,
            },
            {
                "name": "Built-in Speakers",
                "index": 1,
                "hostApi": 0,
                "maxInputChannels": 0,
                "maxOutputChannels": 2,
                "defaultSampleRate": 44100.0,
            },
            {
                "name": "BlackHole 2ch",
                "index": 2,
                "hostApi": 0,
                "maxInputChannels": 2,
                "maxOutputChannels": 2,
                "defaultSampleRate": 48000.0,
            },
            {
                "name": "External USB Microphone",
                "index": 3,
                "hostApi": 0,
                "maxInputChannels": 1,
                "maxOutputChannels": 0,
                "defaultSampleRate": 48000.0,
            },
            {
                "name": "VB-Audio Virtual Cable",
                "index": 4,
                "hostApi": 0,
                "maxInputChannels": 2,
                "maxOutputChannels": 2,
                "defaultSampleRate": 44100.0,
            },
            {
                "name": "Headphones",
                "index": 5,
                "hostApi": 0,
                "maxInputChannels": 0,
                "maxOutputChannels": 2,
                "defaultSampleRate": 48000.0,
            },
        ]

        mock_instance.get_device_count.return_value = len(devices)
        mock_instance.get_device_info_by_index.side_effect = lambda i: devices[i]

        # Default devices
        mock_instance.get_default_input_device_info.return_value = devices[0]
        mock_instance.get_default_output_device_info.return_value = devices[1]

        # Host API info
        mock_instance.get_host_api_info_by_index.return_value = {"name": "Core Audio"}

        # Format validation
        mock_pa.paInt16 = 8

        yield mock_pa


@pytest.fixture
def mock_pyaudio_no_defaults():
    """Create a mock PyAudio with no default devices."""
    with patch("src.audio.devices.pyaudio") as mock_pa:
        mock_instance = MagicMock()
        mock_pa.PyAudio.return_value = mock_instance

        # One device only
        devices = [
            {
                "name": "Some Device",
                "index": 0,
                "hostApi": 0,
                "maxInputChannels": 1,
                "maxOutputChannels": 1,
                "defaultSampleRate": 44100.0,
            }
        ]

        mock_instance.get_device_count.return_value = len(devices)
        mock_instance.get_device_info_by_index.side_effect = lambda i: devices[i]

        # No default devices
        mock_instance.get_default_input_device_info.side_effect = OSError(
            "No default input"
        )
        mock_instance.get_default_output_device_info.side_effect = OSError(
            "No default output"
        )

        mock_instance.get_host_api_info_by_index.return_value = {"name": "Core Audio"}
        mock_pa.paInt16 = 8

        yield mock_pa


@pytest.fixture
def mock_pyaudio_empty():
    """Create a mock PyAudio with no devices."""
    with patch("src.audio.devices.pyaudio") as mock_pa:
        mock_instance = MagicMock()
        mock_pa.PyAudio.return_value = mock_instance

        mock_instance.get_device_count.return_value = 0
        mock_instance.get_default_input_device_info.side_effect = OSError(
            "No devices"
        )
        mock_instance.get_default_output_device_info.side_effect = OSError(
            "No devices"
        )

        mock_pa.paInt16 = 8

        yield mock_pa


@pytest.fixture
def sample_audio_device():
    """Create a sample AudioDevice for testing."""
    return AudioDevice(
        index=0,
        name="Test Device",
        host_api="Core Audio",
        max_input_channels=2,
        max_output_channels=2,
        default_sample_rate=44100.0,
        device_type=DeviceType.INPUT,
        is_default_input=False,
        is_default_output=False,
    )


# ============================================================================
# DeviceType Tests
# ============================================================================


class TestDeviceType:
    """Tests for DeviceType enum."""

    def test_device_types_exist(self):
        """Test all expected device types exist."""
        assert DeviceType.INPUT
        assert DeviceType.OUTPUT
        assert DeviceType.LOOPBACK
        assert DeviceType.UNKNOWN

    def test_device_type_values(self):
        """Test device type string values."""
        assert DeviceType.INPUT.value == "input"
        assert DeviceType.OUTPUT.value == "output"
        assert DeviceType.LOOPBACK.value == "loopback"
        assert DeviceType.UNKNOWN.value == "unknown"


# ============================================================================
# AudioDevice Tests
# ============================================================================


class TestAudioDevice:
    """Tests for AudioDevice dataclass."""

    def test_audio_device_creation(self, sample_audio_device):
        """Test creating an AudioDevice with valid parameters."""
        device = sample_audio_device

        assert device.index == 0
        assert device.name == "Test Device"
        assert device.host_api == "Core Audio"
        assert device.max_input_channels == 2
        assert device.max_output_channels == 2
        assert device.default_sample_rate == 44100.0
        assert device.device_type == DeviceType.INPUT

    def test_is_input_device_property(self):
        """Test is_input_device property."""
        input_device = AudioDevice(
            index=0,
            name="Mic",
            host_api="Core Audio",
            max_input_channels=2,
            max_output_channels=0,
            default_sample_rate=44100.0,
            device_type=DeviceType.INPUT,
        )
        assert input_device.is_input_device is True

        output_device = AudioDevice(
            index=1,
            name="Speaker",
            host_api="Core Audio",
            max_input_channels=0,
            max_output_channels=2,
            default_sample_rate=44100.0,
            device_type=DeviceType.OUTPUT,
        )
        assert output_device.is_input_device is False

    def test_is_output_device_property(self):
        """Test is_output_device property."""
        input_device = AudioDevice(
            index=0,
            name="Mic",
            host_api="Core Audio",
            max_input_channels=2,
            max_output_channels=0,
            default_sample_rate=44100.0,
            device_type=DeviceType.INPUT,
        )
        assert input_device.is_output_device is False

        output_device = AudioDevice(
            index=1,
            name="Speaker",
            host_api="Core Audio",
            max_input_channels=0,
            max_output_channels=2,
            default_sample_rate=44100.0,
            device_type=DeviceType.OUTPUT,
        )
        assert output_device.is_output_device is True

    def test_is_virtual_device_blackhole(self):
        """Test is_virtual_device detects BlackHole."""
        device = AudioDevice(
            index=0,
            name="BlackHole 2ch",
            host_api="Core Audio",
            max_input_channels=2,
            max_output_channels=2,
            default_sample_rate=48000.0,
            device_type=DeviceType.LOOPBACK,
        )
        assert device.is_virtual_device is True

    def test_is_virtual_device_vb_audio(self):
        """Test is_virtual_device detects VB-Audio."""
        device = AudioDevice(
            index=0,
            name="VB-Audio Virtual Cable",
            host_api="MME",
            max_input_channels=2,
            max_output_channels=2,
            default_sample_rate=44100.0,
            device_type=DeviceType.LOOPBACK,
        )
        assert device.is_virtual_device is True

    def test_is_virtual_device_voicemeeter(self):
        """Test is_virtual_device detects VoiceMeeter."""
        device = AudioDevice(
            index=0,
            name="VoiceMeeter Input",
            host_api="MME",
            max_input_channels=2,
            max_output_channels=2,
            default_sample_rate=44100.0,
            device_type=DeviceType.LOOPBACK,
        )
        assert device.is_virtual_device is True

    def test_is_virtual_device_soundflower(self):
        """Test is_virtual_device detects SoundFlower."""
        device = AudioDevice(
            index=0,
            name="Soundflower (2ch)",
            host_api="Core Audio",
            max_input_channels=2,
            max_output_channels=2,
            default_sample_rate=44100.0,
            device_type=DeviceType.LOOPBACK,
        )
        assert device.is_virtual_device is True

    def test_is_virtual_device_regular(self):
        """Test is_virtual_device returns False for regular devices."""
        device = AudioDevice(
            index=0,
            name="Built-in Microphone",
            host_api="Core Audio",
            max_input_channels=2,
            max_output_channels=0,
            default_sample_rate=44100.0,
            device_type=DeviceType.INPUT,
        )
        assert device.is_virtual_device is False

    def test_str_representation_basic(self):
        """Test string representation of AudioDevice."""
        device = AudioDevice(
            index=0,
            name="Test Mic",
            host_api="Core Audio",
            max_input_channels=2,
            max_output_channels=0,
            default_sample_rate=44100.0,
            device_type=DeviceType.INPUT,
        )
        s = str(device)

        assert "[0]" in s
        assert "Test Mic" in s
        assert "in: 2" in s
        assert "out: 0" in s
        assert "44100Hz" in s

    def test_str_representation_with_markers(self):
        """Test string representation includes markers."""
        device = AudioDevice(
            index=0,
            name="BlackHole 2ch",
            host_api="Core Audio",
            max_input_channels=2,
            max_output_channels=2,
            default_sample_rate=48000.0,
            device_type=DeviceType.LOOPBACK,
            is_default_input=True,
            is_default_output=False,
        )
        s = str(device)

        assert "default input" in s
        assert "virtual" in s


# ============================================================================
# AudioDeviceManager Tests
# ============================================================================


class TestAudioDeviceManager:
    """Tests for AudioDeviceManager class."""

    def test_initialization(self, mock_pyaudio):
        """Test AudioDeviceManager initialization."""
        manager = AudioDeviceManager()

        assert manager._pyaudio is None
        assert manager._devices == []
        assert manager._default_input_index is None
        assert manager._default_output_index is None

    def test_context_manager(self, mock_pyaudio):
        """Test AudioDeviceManager as context manager."""
        with AudioDeviceManager() as manager:
            assert manager._pyaudio is not None
            assert len(manager._devices) > 0

        # After context, should be cleaned up
        assert manager._pyaudio is None
        assert len(manager._devices) == 0

    def test_initialize_scans_devices(self, mock_pyaudio):
        """Test initialize() scans available devices."""
        manager = AudioDeviceManager()
        manager.initialize()

        assert len(manager._devices) == 6  # Based on mock_pyaudio fixture

        manager.cleanup()

    def test_initialize_finds_defaults(self, mock_pyaudio):
        """Test initialize() finds default devices."""
        manager = AudioDeviceManager()
        manager.initialize()

        assert manager._default_input_index == 0  # Built-in Mic
        assert manager._default_output_index == 1  # Built-in Speakers

        manager.cleanup()

    def test_initialize_handles_no_defaults(self, mock_pyaudio_no_defaults):
        """Test initialize() handles missing default devices."""
        manager = AudioDeviceManager()
        manager.initialize()

        assert manager._default_input_index is None
        assert manager._default_output_index is None

        manager.cleanup()

    def test_initialize_already_initialized(self, mock_pyaudio):
        """Test initialize() is idempotent."""
        manager = AudioDeviceManager()
        manager.initialize()
        manager.initialize()  # Should not raise

        assert len(manager._devices) == 6

        manager.cleanup()

    def test_cleanup(self, mock_pyaudio):
        """Test cleanup() releases resources."""
        manager = AudioDeviceManager()
        manager.initialize()
        manager.cleanup()

        assert manager._pyaudio is None
        assert len(manager._devices) == 0

    def test_get_all_devices(self, mock_pyaudio):
        """Test get_all_devices() returns all devices."""
        with AudioDeviceManager() as manager:
            devices = manager.get_all_devices()

            assert len(devices) == 6
            assert all(isinstance(d, AudioDevice) for d in devices)

    def test_get_all_devices_returns_copy(self, mock_pyaudio):
        """Test get_all_devices() returns a copy."""
        with AudioDeviceManager() as manager:
            devices1 = manager.get_all_devices()
            devices2 = manager.get_all_devices()

            # Should be different list objects
            assert devices1 is not devices2
            assert devices1 is not manager._devices

    def test_get_input_devices(self, mock_pyaudio):
        """Test get_input_devices() returns only input devices."""
        with AudioDeviceManager() as manager:
            devices = manager.get_input_devices()

            # Built-in Mic, BlackHole, External USB Mic, VB-Audio
            assert len(devices) == 4
            assert all(d.is_input_device for d in devices)

    def test_get_input_devices_exclude_virtual(self, mock_pyaudio):
        """Test get_input_devices() can exclude virtual devices."""
        with AudioDeviceManager() as manager:
            devices = manager.get_input_devices(include_virtual=False)

            # Built-in Mic, External USB Mic (excludes BlackHole, VB-Audio)
            assert len(devices) == 2
            assert all(not d.is_virtual_device for d in devices)

    def test_get_output_devices(self, mock_pyaudio):
        """Test get_output_devices() returns only output devices."""
        with AudioDeviceManager() as manager:
            devices = manager.get_output_devices()

            # Built-in Speakers, BlackHole, VB-Audio, Headphones
            assert len(devices) == 4
            assert all(d.is_output_device for d in devices)

    def test_get_output_devices_exclude_virtual(self, mock_pyaudio):
        """Test get_output_devices() can exclude virtual devices."""
        with AudioDeviceManager() as manager:
            devices = manager.get_output_devices(include_virtual=False)

            # Built-in Speakers, Headphones
            assert len(devices) == 2
            assert all(not d.is_virtual_device for d in devices)

    def test_get_loopback_devices(self, mock_pyaudio):
        """Test get_loopback_devices() returns virtual devices."""
        with AudioDeviceManager() as manager:
            devices = manager.get_loopback_devices()

            # BlackHole, VB-Audio
            assert len(devices) == 2
            assert all(d.is_virtual_device for d in devices)

    def test_get_device_by_index(self, mock_pyaudio):
        """Test get_device_by_index() returns correct device."""
        with AudioDeviceManager() as manager:
            device = manager.get_device_by_index(2)

            assert device is not None
            assert device.name == "BlackHole 2ch"
            assert device.index == 2

    def test_get_device_by_index_not_found(self, mock_pyaudio):
        """Test get_device_by_index() returns None for invalid index."""
        with AudioDeviceManager() as manager:
            device = manager.get_device_by_index(999)

            assert device is None

    def test_get_device_by_name_partial_match(self, mock_pyaudio):
        """Test get_device_by_name() finds partial matches."""
        with AudioDeviceManager() as manager:
            device = manager.get_device_by_name("blackhole")

            assert device is not None
            assert device.name == "BlackHole 2ch"

    def test_get_device_by_name_exact_match(self, mock_pyaudio):
        """Test get_device_by_name() with exact match."""
        with AudioDeviceManager() as manager:
            device = manager.get_device_by_name("BlackHole 2ch", exact_match=True)

            assert device is not None
            assert device.name == "BlackHole 2ch"

    def test_get_device_by_name_exact_match_not_found(self, mock_pyaudio):
        """Test get_device_by_name() exact match returns None if not exact."""
        with AudioDeviceManager() as manager:
            device = manager.get_device_by_name("blackhole", exact_match=True)

            assert device is None  # Case doesn't match exactly

    def test_get_device_by_name_not_found(self, mock_pyaudio):
        """Test get_device_by_name() returns None for unknown device."""
        with AudioDeviceManager() as manager:
            device = manager.get_device_by_name("NonExistent Device")

            assert device is None

    def test_get_default_input_device(self, mock_pyaudio):
        """Test get_default_input_device() returns correct device."""
        with AudioDeviceManager() as manager:
            device = manager.get_default_input_device()

            assert device is not None
            assert device.name == "Built-in Microphone"
            assert device.is_default_input is True

    def test_get_default_output_device(self, mock_pyaudio):
        """Test get_default_output_device() returns correct device."""
        with AudioDeviceManager() as manager:
            device = manager.get_default_output_device()

            assert device is not None
            assert device.name == "Built-in Speakers"
            assert device.is_default_output is True

    def test_get_default_input_device_none(self, mock_pyaudio_no_defaults):
        """Test get_default_input_device() returns None when no default."""
        with AudioDeviceManager() as manager:
            device = manager.get_default_input_device()

            assert device is None

    def test_get_default_output_device_none(self, mock_pyaudio_no_defaults):
        """Test get_default_output_device() returns None when no default."""
        with AudioDeviceManager() as manager:
            device = manager.get_default_output_device()

            assert device is None

    def test_find_blackhole_device(self, mock_pyaudio):
        """Test find_blackhole_device() finds BlackHole."""
        with AudioDeviceManager() as manager:
            device = manager.find_blackhole_device()

            assert device is not None
            assert "blackhole" in device.name.lower()

    def test_find_vb_audio_device(self, mock_pyaudio):
        """Test find_vb_audio_device() finds VB-Audio."""
        with AudioDeviceManager() as manager:
            device = manager.find_vb_audio_device()

            assert device is not None
            assert "vb-audio" in device.name.lower()

    def test_validate_device_config_valid(self, mock_pyaudio):
        """Test validate_device_config() returns True for valid config."""
        mock_pyaudio.PyAudio.return_value.is_format_supported.return_value = True

        with AudioDeviceManager() as manager:
            is_valid = manager.validate_device_config(
                device_index=0,
                sample_rate=44100,
                channels=1,
                is_input=True,
            )

            assert is_valid is True

    def test_validate_device_config_invalid_channels(self, mock_pyaudio):
        """Test validate_device_config() rejects too many channels."""
        with AudioDeviceManager() as manager:
            # Device 0 has max 2 input channels
            is_valid = manager.validate_device_config(
                device_index=0,
                sample_rate=44100,
                channels=8,  # Too many
                is_input=True,
            )

            assert is_valid is False

    def test_validate_device_config_invalid_device(self, mock_pyaudio):
        """Test validate_device_config() returns False for invalid device."""
        with AudioDeviceManager() as manager:
            is_valid = manager.validate_device_config(
                device_index=999,  # Invalid
                sample_rate=44100,
                channels=1,
                is_input=True,
            )

            assert is_valid is False

    def test_validate_device_config_format_not_supported(self, mock_pyaudio):
        """Test validate_device_config() returns False when format unsupported."""
        mock_pyaudio.PyAudio.return_value.is_format_supported.side_effect = ValueError(
            "Format not supported"
        )

        with AudioDeviceManager() as manager:
            is_valid = manager.validate_device_config(
                device_index=0,
                sample_rate=96000,  # Might not be supported
                channels=1,
                is_input=True,
            )

            assert is_valid is False

    def test_validate_device_config_not_initialized(self, mock_pyaudio):
        """Test validate_device_config() raises if not initialized."""
        manager = AudioDeviceManager()

        with pytest.raises(RuntimeError, match="not initialized"):
            manager.validate_device_config(
                device_index=0,
                sample_rate=44100,
                channels=1,
                is_input=True,
            )


# ============================================================================
# Convenience Function Tests
# ============================================================================


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_list_audio_devices(self, mock_pyaudio):
        """Test list_audio_devices() returns all devices."""
        devices = list_audio_devices()

        assert len(devices) == 6
        assert all(isinstance(d, AudioDevice) for d in devices)

    def test_list_audio_devices_empty(self, mock_pyaudio_empty):
        """Test list_audio_devices() handles no devices."""
        devices = list_audio_devices()

        assert len(devices) == 0

    def test_find_microphone_device_default(self, mock_pyaudio):
        """Test find_microphone_device() finds default mic."""
        device = find_microphone_device()

        assert device is not None
        assert device.name == "Built-in Microphone"

    def test_find_microphone_device_by_name(self, mock_pyaudio):
        """Test find_microphone_device() finds by name."""
        device = find_microphone_device("External USB")

        assert device is not None
        assert "External USB" in device.name

    def test_find_microphone_device_not_found(self, mock_pyaudio):
        """Test find_microphone_device() returns None if not found."""
        device = find_microphone_device("NonExistent Mic")

        assert device is None

    def test_find_loopback_device_blackhole(self, mock_pyaudio):
        """Test find_loopback_device() finds BlackHole first."""
        device = find_loopback_device()

        assert device is not None
        assert "blackhole" in device.name.lower()

    def test_find_loopback_device_vb_audio(self, mock_pyaudio):
        """Test find_loopback_device() falls back to VB-Audio."""
        # Remove BlackHole from mock
        mock_pyaudio.PyAudio.return_value.get_device_count.return_value = 5
        original_side_effect = (
            mock_pyaudio.PyAudio.return_value.get_device_info_by_index.side_effect
        )

        devices = [
            {
                "name": "Built-in Microphone",
                "index": 0,
                "hostApi": 0,
                "maxInputChannels": 2,
                "maxOutputChannels": 0,
                "defaultSampleRate": 44100.0,
            },
            {
                "name": "Built-in Speakers",
                "index": 1,
                "hostApi": 0,
                "maxInputChannels": 0,
                "maxOutputChannels": 2,
                "defaultSampleRate": 44100.0,
            },
            {
                "name": "VB-Audio Virtual Cable",
                "index": 2,
                "hostApi": 0,
                "maxInputChannels": 2,
                "maxOutputChannels": 2,
                "defaultSampleRate": 44100.0,
            },
        ]

        mock_pyaudio.PyAudio.return_value.get_device_count.return_value = len(devices)
        mock_pyaudio.PyAudio.return_value.get_device_info_by_index.side_effect = (
            lambda i: devices[i]
        )

        device = find_loopback_device()

        assert device is not None
        assert "vb-audio" in device.name.lower() or "cable" in device.name.lower()

    def test_find_loopback_device_none(self, mock_pyaudio):
        """Test find_loopback_device() returns None if no virtual devices."""
        # Mock with no virtual devices
        devices = [
            {
                "name": "Built-in Microphone",
                "index": 0,
                "hostApi": 0,
                "maxInputChannels": 2,
                "maxOutputChannels": 0,
                "defaultSampleRate": 44100.0,
            },
            {
                "name": "Built-in Speakers",
                "index": 1,
                "hostApi": 0,
                "maxInputChannels": 0,
                "maxOutputChannels": 2,
                "defaultSampleRate": 44100.0,
            },
        ]

        mock_pyaudio.PyAudio.return_value.get_device_count.return_value = len(devices)
        mock_pyaudio.PyAudio.return_value.get_device_info_by_index.side_effect = (
            lambda i: devices[i]
        )

        device = find_loopback_device()

        assert device is None

    def test_find_speaker_device_default(self, mock_pyaudio):
        """Test find_speaker_device() finds default speakers."""
        device = find_speaker_device()

        assert device is not None
        assert device.name == "Built-in Speakers"

    def test_find_speaker_device_by_name(self, mock_pyaudio):
        """Test find_speaker_device() finds by name."""
        device = find_speaker_device("Headphones")

        assert device is not None
        assert "Headphones" in device.name

    def test_find_speaker_device_not_output(self, mock_pyaudio):
        """Test find_speaker_device() returns None if device is not output."""
        # Try to find an input device as speaker
        device = find_speaker_device("Built-in Microphone")

        assert device is None  # Mic is not an output device

    def test_find_virtual_mic_device_blackhole(self, mock_pyaudio):
        """Test find_virtual_mic_device() finds BlackHole."""
        device = find_virtual_mic_device()

        assert device is not None
        assert "blackhole" in device.name.lower()

    def test_find_virtual_mic_device_none(self, mock_pyaudio):
        """Test find_virtual_mic_device() returns None if no virtual output."""
        # Mock with no virtual devices
        devices = [
            {
                "name": "Built-in Microphone",
                "index": 0,
                "hostApi": 0,
                "maxInputChannels": 2,
                "maxOutputChannels": 0,
                "defaultSampleRate": 44100.0,
            },
            {
                "name": "Built-in Speakers",
                "index": 1,
                "hostApi": 0,
                "maxInputChannels": 0,
                "maxOutputChannels": 2,
                "defaultSampleRate": 44100.0,
            },
        ]

        mock_pyaudio.PyAudio.return_value.get_device_count.return_value = len(devices)
        mock_pyaudio.PyAudio.return_value.get_device_info_by_index.side_effect = (
            lambda i: devices[i]
        )

        device = find_virtual_mic_device()

        assert device is None


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestDeviceEdgeCases:
    """Edge case and error condition tests."""

    def test_device_error_during_scan(self, mock_pyaudio):
        """Test handling of errors when scanning specific devices."""
        # Make one device raise an error
        original = mock_pyaudio.PyAudio.return_value.get_device_info_by_index

        def flaky_get(i):
            if i == 3:
                raise Exception("Device error")
            return original(i)

        mock_pyaudio.PyAudio.return_value.get_device_info_by_index.side_effect = (
            flaky_get
        )

        with AudioDeviceManager() as manager:
            devices = manager.get_all_devices()

            # Should still have other devices
            assert len(devices) == 5  # One less than usual

    def test_host_api_error(self, mock_pyaudio):
        """Test handling of host API info errors."""
        mock_pyaudio.PyAudio.return_value.get_host_api_info_by_index.side_effect = (
            Exception("No host API")
        )

        with AudioDeviceManager() as manager:
            devices = manager.get_all_devices()

            # Should still have devices, host_api will be "Unknown"
            assert len(devices) == 6
            assert all(d.host_api == "Unknown" for d in devices)

    def test_empty_device_list(self, mock_pyaudio_empty):
        """Test handling of empty device list."""
        with AudioDeviceManager() as manager:
            assert manager.get_all_devices() == []
            assert manager.get_input_devices() == []
            assert manager.get_output_devices() == []
            assert manager.get_loopback_devices() == []

    def test_device_type_classification_both_channels(self, mock_pyaudio):
        """Test device type classification for devices with both I/O."""
        with AudioDeviceManager() as manager:
            blackhole = manager.get_device_by_name("blackhole")

            # BlackHole has both input and output, should be LOOPBACK
            assert blackhole.device_type == DeviceType.LOOPBACK

    def test_device_type_classification_input_only(self, mock_pyaudio):
        """Test device type classification for input-only devices."""
        with AudioDeviceManager() as manager:
            mic = manager.get_device_by_name("built-in mic")

            assert mic.device_type == DeviceType.INPUT

    def test_device_type_classification_output_only(self, mock_pyaudio):
        """Test device type classification for output-only devices."""
        with AudioDeviceManager() as manager:
            speakers = manager.get_device_by_name("built-in speakers")

            assert speakers.device_type == DeviceType.OUTPUT

    def test_device_with_zero_channels(self, mock_pyaudio):
        """Test handling of device with zero channels."""
        devices = [
            {
                "name": "Weird Device",
                "index": 0,
                "hostApi": 0,
                "maxInputChannels": 0,
                "maxOutputChannels": 0,
                "defaultSampleRate": 44100.0,
            }
        ]

        mock_pyaudio.PyAudio.return_value.get_device_count.return_value = 1
        mock_pyaudio.PyAudio.return_value.get_device_info_by_index.side_effect = (
            lambda i: devices[i]
        )
        mock_pyaudio.PyAudio.return_value.get_default_input_device_info.side_effect = (
            OSError("No default")
        )
        mock_pyaudio.PyAudio.return_value.get_default_output_device_info.side_effect = (
            OSError("No default")
        )

        with AudioDeviceManager() as manager:
            device = manager.get_device_by_index(0)

            assert device is not None
            assert device.device_type == DeviceType.UNKNOWN
            assert device.is_input_device is False
            assert device.is_output_device is False


# ============================================================================
# Print/Debug Tests
# ============================================================================


class TestPrintFunctions:
    """Tests for print/debug functions."""

    def test_print_all_devices(self, mock_pyaudio, capsys):
        """Test print_all_devices() outputs device info."""
        with AudioDeviceManager() as manager:
            manager.print_all_devices()

        captured = capsys.readouterr()

        assert "Available Audio Devices" in captured.out
        assert "Input Devices" in captured.out
        assert "Output Devices" in captured.out
        assert "Built-in Microphone" in captured.out
        assert "Built-in Speakers" in captured.out
