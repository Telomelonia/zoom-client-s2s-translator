"""
Audio device enumeration and management.

Provides utilities for discovering and selecting audio input/output devices.
Helps users configure microphone and loopback devices for translation.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

import pyaudio

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """Audio device type classification."""

    INPUT = "input"
    OUTPUT = "output"
    LOOPBACK = "loopback"  # Virtual audio device for system capture
    UNKNOWN = "unknown"


@dataclass
class AudioDevice:
    """
    Audio device information.

    Represents a physical or virtual audio device available on the system.
    """

    index: int
    name: str
    host_api: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: float
    device_type: DeviceType
    is_default_input: bool = False
    is_default_output: bool = False

    @property
    def is_input_device(self) -> bool:
        """Check if device supports input (recording)."""
        return self.max_input_channels > 0

    @property
    def is_output_device(self) -> bool:
        """Check if device supports output (playback)."""
        return self.max_output_channels > 0

    @property
    def is_virtual_device(self) -> bool:
        """
        Check if this appears to be a virtual audio device.

        Heuristic: device name contains common virtual device keywords.
        """
        virtual_keywords = [
            "blackhole",
            "vb-audio",
            "virtual",
            "loopback",
            "cable",
            "voicemeeter",
            "soundflower",
        ]
        name_lower = self.name.lower()
        return any(keyword in name_lower for keyword in virtual_keywords)

    def __str__(self) -> str:
        """Human-readable device description."""
        markers = []
        if self.is_default_input:
            markers.append("default input")
        if self.is_default_output:
            markers.append("default output")
        if self.is_virtual_device:
            markers.append("virtual")

        marker_str = f" [{', '.join(markers)}]" if markers else ""

        return (
            f"[{self.index}] {self.name} "
            f"(in: {self.max_input_channels}, out: {self.max_output_channels}, "
            f"{int(self.default_sample_rate)}Hz){marker_str}"
        )


class AudioDeviceManager:
    """
    Manages audio device discovery and selection.

    Provides methods to enumerate devices, find specific devices,
    and validate device configurations.
    """

    def __init__(self):
        """Initialize the audio device manager."""
        self._pyaudio: Optional[pyaudio.PyAudio] = None
        self._devices: List[AudioDevice] = []
        self._default_input_index: Optional[int] = None
        self._default_output_index: Optional[int] = None

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

    def initialize(self) -> None:
        """
        Initialize PyAudio and scan available devices.

        Must be called before using other methods.
        """
        if self._pyaudio is not None:
            logger.warning("AudioDeviceManager already initialized")
            return

        self._pyaudio = pyaudio.PyAudio()
        self._scan_devices()
        logger.info(f"AudioDeviceManager initialized, found {len(self._devices)} devices")

    def cleanup(self) -> None:
        """Clean up PyAudio resources."""
        if self._pyaudio:
            self._pyaudio.terminate()
            self._pyaudio = None
            self._devices.clear()

    def _scan_devices(self) -> None:
        """Scan and categorize all available audio devices."""
        if not self._pyaudio:
            raise RuntimeError("PyAudio not initialized")

        self._devices.clear()

        # Get default devices
        try:
            self._default_input_index = self._pyaudio.get_default_input_device_info()[
                "index"
            ]
        except OSError:
            logger.warning("No default input device found")
            self._default_input_index = None

        try:
            self._default_output_index = self._pyaudio.get_default_output_device_info()[
                "index"
            ]
        except OSError:
            logger.warning("No default output device found")
            self._default_output_index = None

        # Enumerate all devices
        device_count = self._pyaudio.get_device_count()

        for i in range(device_count):
            try:
                info = self._pyaudio.get_device_info_by_index(i)
                device = self._create_device_from_info(i, info)
                self._devices.append(device)

                logger.debug(f"Found device: {device}")

            except Exception as e:
                logger.warning(f"Error reading device {i}: {e}")

    def _create_device_from_info(self, index: int, info: Dict[str, Any]) -> AudioDevice:
        """
        Create AudioDevice from PyAudio device info.

        Args:
            index: Device index
            info: PyAudio device info dictionary

        Returns:
            AudioDevice instance
        """
        # Get host API name
        host_api_index = info.get("hostApi", 0)
        try:
            host_api_info = self._pyaudio.get_host_api_info_by_index(host_api_index)
            host_api_name = host_api_info.get("name", "Unknown")
        except Exception:
            host_api_name = "Unknown"

        # Determine device type
        max_in = info.get("maxInputChannels", 0)
        max_out = info.get("maxOutputChannels", 0)

        device_type = DeviceType.UNKNOWN
        if max_in > 0 and max_out == 0:
            device_type = DeviceType.INPUT
        elif max_out > 0 and max_in == 0:
            device_type = DeviceType.OUTPUT
        elif max_in > 0 and max_out > 0:
            # Could be loopback or full-duplex device
            name_lower = info.get("name", "").lower()
            if any(
                kw in name_lower
                for kw in ["blackhole", "loopback", "cable", "virtual"]
            ):
                device_type = DeviceType.LOOPBACK
            else:
                device_type = DeviceType.INPUT  # Assume input if both

        return AudioDevice(
            index=index,
            name=info.get("name", f"Device {index}"),
            host_api=host_api_name,
            max_input_channels=max_in,
            max_output_channels=max_out,
            default_sample_rate=info.get("defaultSampleRate", 44100.0),
            device_type=device_type,
            is_default_input=(index == self._default_input_index),
            is_default_output=(index == self._default_output_index),
        )

    def get_all_devices(self) -> List[AudioDevice]:
        """
        Get list of all available audio devices.

        Returns:
            List of AudioDevice instances
        """
        return self._devices.copy()

    def get_input_devices(self, include_virtual: bool = True) -> List[AudioDevice]:
        """
        Get list of all input (recording) devices.

        Args:
            include_virtual: Include virtual audio devices

        Returns:
            List of input-capable AudioDevice instances
        """
        devices = [d for d in self._devices if d.is_input_device]

        if not include_virtual:
            devices = [d for d in devices if not d.is_virtual_device]

        return devices

    def get_output_devices(self, include_virtual: bool = True) -> List[AudioDevice]:
        """
        Get list of all output (playback) devices.

        Args:
            include_virtual: Include virtual audio devices

        Returns:
            List of output-capable AudioDevice instances
        """
        devices = [d for d in self._devices if d.is_output_device]

        if not include_virtual:
            devices = [d for d in devices if not d.is_virtual_device]

        return devices

    def get_loopback_devices(self) -> List[AudioDevice]:
        """
        Get list of virtual audio devices suitable for system audio capture.

        Returns:
            List of virtual AudioDevice instances (BlackHole, VB-Audio, etc.)
        """
        return [d for d in self._devices if d.is_virtual_device and d.is_input_device]

    def get_device_by_index(self, index: int) -> Optional[AudioDevice]:
        """
        Get device by its index.

        Args:
            index: PyAudio device index

        Returns:
            AudioDevice if found, None otherwise
        """
        for device in self._devices:
            if device.index == index:
                return device
        return None

    def get_device_by_name(
        self, name: str, exact_match: bool = False
    ) -> Optional[AudioDevice]:
        """
        Get device by name.

        Args:
            name: Device name (or partial name if exact_match=False)
            exact_match: Require exact name match

        Returns:
            First matching AudioDevice, or None if not found
        """
        name_lower = name.lower()

        for device in self._devices:
            device_name_lower = device.name.lower()

            if exact_match:
                if device_name_lower == name_lower:
                    return device
            else:
                if name_lower in device_name_lower:
                    return device

        return None

    def get_default_input_device(self) -> Optional[AudioDevice]:
        """
        Get the system default input device.

        Returns:
            Default input AudioDevice, or None if not available
        """
        if self._default_input_index is not None:
            return self.get_device_by_index(self._default_input_index)
        return None

    def get_default_output_device(self) -> Optional[AudioDevice]:
        """
        Get the system default output device.

        Returns:
            Default output AudioDevice, or None if not available
        """
        if self._default_output_index is not None:
            return self.get_device_by_index(self._default_output_index)
        return None

    def find_blackhole_device(self) -> Optional[AudioDevice]:
        """
        Find BlackHole virtual audio device (macOS).

        Returns:
            BlackHole AudioDevice if found, None otherwise
        """
        return self.get_device_by_name("blackhole")

    def find_vb_audio_device(self) -> Optional[AudioDevice]:
        """
        Find VB-Audio Cable device (Windows).

        Returns:
            VB-Audio AudioDevice if found, None otherwise
        """
        vb_device = self.get_device_by_name("cable")
        if vb_device and "vb-audio" in vb_device.name.lower():
            return vb_device

        return self.get_device_by_name("vb-audio")

    def validate_device_config(
        self,
        device_index: int,
        sample_rate: int,
        channels: int,
        is_input: bool = True,
    ) -> bool:
        """
        Validate if a device supports the specified configuration.

        Args:
            device_index: PyAudio device index
            sample_rate: Desired sample rate in Hz
            channels: Number of channels
            is_input: True for input device, False for output

        Returns:
            True if configuration is supported, False otherwise
        """
        if not self._pyaudio:
            raise RuntimeError("PyAudio not initialized")

        device = self.get_device_by_index(device_index)
        if not device:
            logger.error(f"Device {device_index} not found")
            return False

        # Check channel count
        max_channels = (
            device.max_input_channels if is_input else device.max_output_channels
        )
        if channels > max_channels:
            logger.error(
                f"Device {device.name} supports max {max_channels} channels, "
                f"requested {channels}"
            )
            return False

        # Try to validate with PyAudio
        try:
            supported = self._pyaudio.is_format_supported(
                sample_rate,
                input_device=device_index if is_input else None,
                output_device=device_index if not is_input else None,
                input_channels=channels if is_input else None,
                output_channels=channels if not is_input else None,
                input_format=pyaudio.paInt16,
                output_format=pyaudio.paInt16,
            )
            return supported
        except ValueError as e:
            logger.error(f"Device configuration not supported: {e}")
            return False

    def print_all_devices(self) -> None:
        """Print all available devices to console (for debugging)."""
        print("\n=== Available Audio Devices ===\n")

        input_devices = self.get_input_devices()
        output_devices = self.get_output_devices()
        loopback_devices = self.get_loopback_devices()

        print(f"Input Devices ({len(input_devices)}):")
        for device in input_devices:
            print(f"  {device}")

        print(f"\nOutput Devices ({len(output_devices)}):")
        for device in output_devices:
            print(f"  {device}")

        if loopback_devices:
            print(f"\nVirtual/Loopback Devices ({len(loopback_devices)}):")
            for device in loopback_devices:
                print(f"  {device}")

        print("\n===============================\n")


# Convenience functions for quick access
def list_audio_devices() -> List[AudioDevice]:
    """
    List all available audio devices.

    Returns:
        List of AudioDevice instances

    Example:
        ```python
        devices = list_audio_devices()
        for device in devices:
            print(device)
        ```
    """
    with AudioDeviceManager() as manager:
        return manager.get_all_devices()


def find_microphone_device(name: Optional[str] = None) -> Optional[AudioDevice]:
    """
    Find a microphone device.

    Args:
        name: Device name to search for (None = default device)

    Returns:
        AudioDevice if found, None otherwise
    """
    with AudioDeviceManager() as manager:
        if name:
            return manager.get_device_by_name(name)
        else:
            return manager.get_default_input_device()


def find_loopback_device() -> Optional[AudioDevice]:
    """
    Find a virtual audio device for system audio capture.

    Tries to find BlackHole (macOS) or VB-Audio (Windows) automatically.

    Returns:
        AudioDevice if found, None otherwise
    """
    with AudioDeviceManager() as manager:
        # Try BlackHole first (macOS)
        device = manager.find_blackhole_device()
        if device:
            return device

        # Try VB-Audio (Windows)
        device = manager.find_vb_audio_device()
        if device:
            return device

        # Return first virtual device found
        loopback_devices = manager.get_loopback_devices()
        if loopback_devices:
            return loopback_devices[0]

        return None


def find_speaker_device(name: Optional[str] = None) -> Optional[AudioDevice]:
    """
    Find a speaker (output) device.

    Args:
        name: Device name to search for (None = default output device)

    Returns:
        AudioDevice if found, None otherwise

    Example:
        ```python
        speaker = find_speaker_device()
        if speaker:
            print(f"Default speaker: {speaker.name}")
        ```
    """
    with AudioDeviceManager() as manager:
        if name:
            device = manager.get_device_by_name(name)
            if device and device.is_output_device:
                return device
            return None
        else:
            return manager.get_default_output_device()


def find_virtual_mic_device() -> Optional[AudioDevice]:
    """
    Find a virtual audio device suitable for routing audio to Zoom.

    This looks for virtual output devices (BlackHole, VB-Audio, etc.)
    that can be selected as an input device in Zoom.

    Returns:
        AudioDevice if found, None otherwise

    Example:
        ```python
        virtual_mic = find_virtual_mic_device()
        if virtual_mic:
            print(f"Use device index {virtual_mic.index} for VirtualMicOutput")
        ```
    """
    with AudioDeviceManager() as manager:
        # Look for virtual devices that support output
        # (output from our app = input for other apps like Zoom)

        # Try BlackHole first (macOS)
        device = manager.get_device_by_name("blackhole")
        if device and device.is_output_device:
            return device

        # Try VB-Audio (Windows)
        device = manager.get_device_by_name("cable input")
        if device and device.is_output_device:
            return device

        device = manager.get_device_by_name("vb-audio")
        if device and device.is_output_device:
            return device

        # Return first virtual output device found
        for device in manager.get_output_devices():
            if device.is_virtual_device:
                return device

        return None


# CLI utility for testing
if __name__ == "__main__":
    """Print all available audio devices when run as script."""
    logging.basicConfig(level=logging.INFO)

    print("Scanning audio devices...\n")

    with AudioDeviceManager() as manager:
        manager.print_all_devices()

        # Show defaults
        default_in = manager.get_default_input_device()
        if default_in:
            print(f"Default Input: {default_in}")

        default_out = manager.get_default_output_device()
        if default_out:
            print(f"Default Output: {default_out}")

        # Show virtual devices
        loopback = find_loopback_device()
        if loopback:
            print(f"\nRecommended Loopback Device: {loopback}")
        else:
            print("\nNo virtual audio device found!")
            print("Install BlackHole (macOS) or VB-Audio Cable (Windows)")
