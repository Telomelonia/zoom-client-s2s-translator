"""
Gemini API integration module.

Handles WebSocket connection to Vertex AI Gemini Live API
for speech-to-speech translation.
"""

from typing import Final

# Gemini API configuration
GEMINI_MODEL: Final[str] = "gemini-2.5-flash-s2st-exp-11-2025"
GEMINI_API_VERSION: Final[str] = "v1alpha"

__all__ = [
    "GEMINI_MODEL",
    "GEMINI_API_VERSION",
]
