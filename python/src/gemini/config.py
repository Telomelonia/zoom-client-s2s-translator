"""
Gemini API configuration module.

Configuration dataclasses and supported language definitions for
speech-to-speech translation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SupportedLanguage(Enum):
    """
    Supported languages for Gemini S2ST translation.

    Each enum value represents a BCP-47 language code supported by
    the Gemini Live API for speech-to-speech translation.
    """

    # Major languages
    ENGLISH_US = "en-US"
    JAPANESE = "ja-JP"
    SPANISH = "es-ES"
    FRENCH = "fr-FR"
    GERMAN = "de-DE"
    ITALIAN = "it-IT"
    PORTUGUESE_BR = "pt-BR"
    PORTUGUESE_PT = "pt-PT"
    RUSSIAN = "ru-RU"

    # Asian languages
    CHINESE_MANDARIN = "cmn-CN"
    CHINESE_CANTONESE = "yue-HK"
    KOREAN = "ko-KR"
    HINDI = "hi-IN"
    BENGALI = "bn-IN"
    TAMIL = "ta-IN"
    TELUGU = "te-IN"
    MARATHI = "mr-IN"
    GUJARATI = "gu-IN"
    THAI = "th-TH"
    VIETNAMESE = "vi-VN"
    INDONESIAN = "id-ID"
    MALAY = "ms-MY"

    # Middle Eastern languages
    ARABIC = "ar-XA"
    HEBREW = "he-IL"
    TURKISH = "tr-TR"
    PERSIAN = "fa-IR"

    # European languages
    DUTCH = "nl-NL"
    POLISH = "pl-PL"
    SWEDISH = "sv-SE"
    NORWEGIAN = "nb-NO"
    DANISH = "da-DK"
    FINNISH = "fi-FI"
    CZECH = "cs-CZ"
    HUNGARIAN = "hu-HU"
    ROMANIAN = "ro-RO"
    GREEK = "el-GR"
    UKRAINIAN = "uk-UA"

    @property
    def display_name(self) -> str:
        """Get human-readable display name for the language."""
        return _LANGUAGE_DISPLAY_NAMES.get(self, self.value)

    @property
    def language_code(self) -> str:
        """Get the BCP-47 language code."""
        return self.value

    @classmethod
    def from_code(cls, code: str) -> "SupportedLanguage":
        """
        Create SupportedLanguage from language code.

        Args:
            code: BCP-47 language code (e.g., "ja-JP")

        Returns:
            SupportedLanguage enum value

        Raises:
            ValueError: If language code is not supported
        """
        for lang in cls:
            if lang.value == code:
                return lang
        raise ValueError(
            f"Language code '{code}' is not supported. "
            f"See SupportedLanguage enum for valid codes."
        )


# Human-readable display names for languages
_LANGUAGE_DISPLAY_NAMES = {
    SupportedLanguage.ENGLISH_US: "English (US)",
    SupportedLanguage.JAPANESE: "Japanese",
    SupportedLanguage.SPANISH: "Spanish",
    SupportedLanguage.FRENCH: "French",
    SupportedLanguage.GERMAN: "German",
    SupportedLanguage.ITALIAN: "Italian",
    SupportedLanguage.PORTUGUESE_BR: "Portuguese (Brazil)",
    SupportedLanguage.PORTUGUESE_PT: "Portuguese (Portugal)",
    SupportedLanguage.RUSSIAN: "Russian",
    SupportedLanguage.CHINESE_MANDARIN: "Chinese (Mandarin)",
    SupportedLanguage.CHINESE_CANTONESE: "Chinese (Cantonese)",
    SupportedLanguage.KOREAN: "Korean",
    SupportedLanguage.HINDI: "Hindi",
    SupportedLanguage.BENGALI: "Bengali",
    SupportedLanguage.TAMIL: "Tamil",
    SupportedLanguage.TELUGU: "Telugu",
    SupportedLanguage.MARATHI: "Marathi",
    SupportedLanguage.GUJARATI: "Gujarati",
    SupportedLanguage.THAI: "Thai",
    SupportedLanguage.VIETNAMESE: "Vietnamese",
    SupportedLanguage.INDONESIAN: "Indonesian",
    SupportedLanguage.MALAY: "Malay",
    SupportedLanguage.ARABIC: "Arabic",
    SupportedLanguage.HEBREW: "Hebrew",
    SupportedLanguage.TURKISH: "Turkish",
    SupportedLanguage.PERSIAN: "Persian",
    SupportedLanguage.DUTCH: "Dutch",
    SupportedLanguage.POLISH: "Polish",
    SupportedLanguage.SWEDISH: "Swedish",
    SupportedLanguage.NORWEGIAN: "Norwegian",
    SupportedLanguage.DANISH: "Danish",
    SupportedLanguage.FINNISH: "Finnish",
    SupportedLanguage.CZECH: "Czech",
    SupportedLanguage.HUNGARIAN: "Hungarian",
    SupportedLanguage.ROMANIAN: "Romanian",
    SupportedLanguage.GREEK: "Greek",
    SupportedLanguage.UKRAINIAN: "Ukrainian",
}


@dataclass(frozen=True)
class GeminiConfig:
    """
    Immutable configuration for Gemini S2ST client.

    This configuration determines the behavior of the Vertex AI Live API
    connection for speech-to-speech translation, including target language,
    model selection, and optional features like transcription.

    Note: Uses Vertex AI (not Google AI Studio) for free S2ST preview access.
    """

    target_language: SupportedLanguage
    model: str = "gemini-2.5-flash-s2st-exp-11-2025"  # Vertex AI S2ST model (private experimental)
    enable_transcription: bool = False
    enable_affective_dialog: bool = True
    voice_name: Optional[str] = None
    system_instruction: Optional[str] = None

    # Vertex AI configuration
    gcp_project: Optional[str] = None  # Defaults to GOOGLE_CLOUD_PROJECT env var
    gcp_location: str = "us-central1"  # Vertex AI region

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if not isinstance(self.target_language, SupportedLanguage):
            raise ValueError(
                f"target_language must be a SupportedLanguage enum value, "
                f"got {type(self.target_language)}"
            )

    @property
    def language_code(self) -> str:
        """Get the BCP-47 language code for the target language."""
        return self.target_language.language_code

    @property
    def language_display_name(self) -> str:
        """Get human-readable display name for the target language."""
        return self.target_language.display_name


def get_all_languages() -> list[SupportedLanguage]:
    """
    Get list of all supported languages.

    Returns:
        List of all SupportedLanguage enum values
    """
    return list(SupportedLanguage)


def get_language_choices() -> dict[str, SupportedLanguage]:
    """
    Get dictionary of language display names to enum values.

    Useful for CLI or UI selection menus.

    Returns:
        Dictionary mapping display names to SupportedLanguage values

    Example:
        ```python
        choices = get_language_choices()
        for name, lang in choices.items():
            print(f"{name}: {lang.language_code}")
        ```
    """
    return {lang.display_name: lang for lang in SupportedLanguage}


def get_language_by_name(name: str) -> SupportedLanguage | None:
    """
    Find language by display name (case-insensitive).

    Args:
        name: Display name to search for (e.g., "Japanese", "Spanish")

    Returns:
        SupportedLanguage if found, None otherwise

    Example:
        ```python
        lang = get_language_by_name("Japanese")
        if lang:
            print(lang.language_code)  # "ja-JP"
        ```
    """
    name_lower = name.lower()
    for lang in SupportedLanguage:
        if lang.display_name.lower() == name_lower:
            return lang
    return None
