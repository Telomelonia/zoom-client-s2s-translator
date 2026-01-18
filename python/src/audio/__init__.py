"""
Audio processing module.

Handles audio capture from microphone and system audio,
as well as audio output to speakers and virtual microphone.
"""

from typing import Final

# Audio configuration constants
SAMPLE_RATE_MIC: Final[int] = 16000  # Hz
SAMPLE_RATE_SYSTEM: Final[int] = 24000  # Hz
SAMPLE_RATE_OUTPUT: Final[int] = 24000  # Hz
BIT_DEPTH: Final[int] = 16  # bits
CHANNELS: Final[int] = 1  # mono
CHUNK_SIZE: Final[int] = 1024  # frames

# Import main classes
from .capture import (
    MicrophoneCapture,
    SystemAudioCapture,
    AudioChunk,
    CaptureState,
    AudioCaptureError,
    AudioDeviceError,
    AudioStreamError,
)

from .devices import (
    AudioDevice,
    AudioDeviceManager,
    DeviceType,
    list_audio_devices,
    find_microphone_device,
    find_loopback_device,
)

__all__ = [
    # Constants
    "SAMPLE_RATE_MIC",
    "SAMPLE_RATE_SYSTEM",
    "SAMPLE_RATE_OUTPUT",
    "BIT_DEPTH",
    "CHANNELS",
    "CHUNK_SIZE",
    # Capture classes
    "MicrophoneCapture",
    "SystemAudioCapture",
    "AudioChunk",
    "CaptureState",
    "AudioCaptureError",
    "AudioDeviceError",
    "AudioStreamError",
    # Device management
    "AudioDevice",
    "AudioDeviceManager",
    "DeviceType",
    "list_audio_devices",
    "find_microphone_device",
    "find_loopback_device",
]
