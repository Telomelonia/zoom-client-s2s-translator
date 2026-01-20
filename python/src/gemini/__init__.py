"""
Gemini API integration module.

Handles WebSocket connection to Vertex AI Gemini Live API
for real-time speech-to-speech translation.

Note: Uses Vertex AI (not Google AI Studio) for free S2ST preview access.
Authentication via Application Default Credentials (ADC).
"""

from typing import Final

# Vertex AI Gemini S2ST configuration
DEFAULT_MODEL: Final[str] = "gemini-2.5-flash-s2st-11-2025-exp"  # Free S2ST preview model
GEMINI_API_VERSION: Final[str] = "v1"

# Import configuration classes
from .config import (
    GeminiConfig,
    SupportedLanguage,
    get_all_languages,
    get_language_choices,
    get_language_by_name,
)

# Import client
from .client import (
    GeminiS2STClient,
    ConnectionState,
    GeminiStats,
)

# Import error classes
from .errors import (
    GeminiError,
    GeminiConnectionError,
    GeminiAuthenticationError,
    GeminiRateLimitError,
    GeminiSessionExpiredError,
    GeminiAudioError,
    GeminiConfigurationError,
    ReconnectionHandler,
    SessionTimeoutTracker,
    ReconnectionState,
)

__all__ = [
    # Constants
    "DEFAULT_MODEL",
    "GEMINI_API_VERSION",
    # Config
    "GeminiConfig",
    "SupportedLanguage",
    "get_all_languages",
    "get_language_choices",
    "get_language_by_name",
    # Client
    "GeminiS2STClient",
    "ConnectionState",
    "GeminiStats",
    # Errors
    "GeminiError",
    "GeminiConnectionError",
    "GeminiAuthenticationError",
    "GeminiRateLimitError",
    "GeminiSessionExpiredError",
    "GeminiAudioError",
    "GeminiConfigurationError",
    "ReconnectionHandler",
    "SessionTimeoutTracker",
    "ReconnectionState",
]
