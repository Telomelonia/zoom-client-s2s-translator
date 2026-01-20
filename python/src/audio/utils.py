"""
Audio utility functions.

Provides resampling and format conversion utilities for audio processing.
"""

import logging
from typing import Optional
import numpy as np
from scipy import signal

logger = logging.getLogger(__name__)


def resample_audio(
    audio_data: bytes,
    original_rate: int,
    target_rate: int,
    channels: int = 1,
    bit_depth: int = 16,
) -> bytes:
    """
    Resample audio data to a different sample rate.

    Uses scipy.signal.resample for high-quality resampling with anti-aliasing.

    Args:
        audio_data: Raw PCM audio bytes
        original_rate: Original sample rate in Hz
        target_rate: Target sample rate in Hz
        channels: Number of audio channels (1=mono, 2=stereo)
        bit_depth: Bit depth (8, 16, 24, or 32)

    Returns:
        Resampled audio data as bytes

    Example:
        ```python
        # Convert 24kHz audio to 16kHz for Gemini
        audio_16k = resample_audio(audio_24k, 24000, 16000)
        ```
    """
    if original_rate == target_rate:
        return audio_data

    # Determine numpy dtype based on bit depth
    if bit_depth == 16:
        dtype = np.int16
    elif bit_depth == 8:
        dtype = np.int8
    elif bit_depth == 32:
        dtype = np.int32
    else:
        raise ValueError(f"Unsupported bit depth: {bit_depth}")

    # Convert bytes to numpy array
    audio_array = np.frombuffer(audio_data, dtype=dtype)

    # Calculate number of samples after resampling
    original_samples = len(audio_array) // channels
    target_samples = int(original_samples * target_rate / original_rate)

    # Handle multi-channel audio
    if channels == 1:
        # Mono: direct resampling
        resampled = signal.resample(audio_array, target_samples)
    else:
        # Multi-channel: resample each channel separately
        audio_array = audio_array.reshape(-1, channels)
        resampled_channels = []
        for ch in range(channels):
            channel_data = audio_array[:, ch]
            resampled_channel = signal.resample(channel_data, target_samples)
            resampled_channels.append(resampled_channel)

        # Interleave channels back
        resampled = np.column_stack(resampled_channels).flatten()

    # Convert back to original dtype and bytes
    resampled = np.clip(resampled, np.iinfo(dtype).min, np.iinfo(dtype).max)
    resampled = resampled.astype(dtype)

    logger.debug(
        f"Resampled audio: {original_rate}Hz -> {target_rate}Hz "
        f"({len(audio_data)} bytes -> {len(resampled.tobytes())} bytes)"
    )

    return resampled.tobytes()


def convert_to_mono(audio_data: bytes, bit_depth: int = 16) -> bytes:
    """
    Convert stereo audio to mono by averaging channels.

    Args:
        audio_data: Raw PCM audio bytes (stereo)
        bit_depth: Bit depth (8, 16, 24, or 32)

    Returns:
        Mono audio data as bytes
    """
    if bit_depth == 16:
        dtype = np.int16
    elif bit_depth == 8:
        dtype = np.int8
    elif bit_depth == 32:
        dtype = np.int32
    else:
        raise ValueError(f"Unsupported bit depth: {bit_depth}")

    # Convert bytes to int16 array
    audio_array = np.frombuffer(audio_data, dtype=dtype)

    # Reshape to (frames, 2) for stereo
    audio_array = audio_array.reshape(-1, 2)

    # Average channels to get mono
    mono_array = audio_array.mean(axis=1).astype(dtype)

    return mono_array.tobytes()


def calculate_audio_duration(
    data_size_bytes: int,
    sample_rate: int,
    channels: int = 1,
    bit_depth: int = 16,
) -> float:
    """
    Calculate audio duration in seconds from byte size.

    Args:
        data_size_bytes: Size of audio data in bytes
        sample_rate: Sample rate in Hz
        channels: Number of channels
        bit_depth: Bit depth

    Returns:
        Duration in seconds
    """
    bytes_per_sample = (bit_depth // 8) * channels
    num_samples = data_size_bytes / bytes_per_sample
    duration = num_samples / sample_rate
    return duration
