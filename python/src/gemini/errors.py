"""
Gemini API error handling module.

Custom exceptions and reconnection logic for Gemini Live API integration.
"""

import asyncio
import logging
import random
from typing import Callable, Awaitable, Optional
from enum import Enum, auto

logger = logging.getLogger(__name__)


class GeminiError(Exception):
    """Base exception for all Gemini-related errors."""

    pass


class GeminiConnectionError(GeminiError):
    """Failed to establish connection to Gemini API."""

    pass


class GeminiAuthenticationError(GeminiError):
    """Authentication failed (invalid API key or credentials)."""

    pass


class GeminiRateLimitError(GeminiError):
    """Rate limit exceeded for API requests."""

    pass


class GeminiSessionExpiredError(GeminiError):
    """Session expired (typically after 10 minute timeout)."""

    pass


class GeminiAudioError(GeminiError):
    """Error processing or streaming audio data."""

    pass


class GeminiConfigurationError(GeminiError):
    """Invalid configuration parameters."""

    pass


class ReconnectionState(Enum):
    """Reconnection attempt state."""

    IDLE = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    FAILED = auto()


class ReconnectionHandler:
    """
    Handles automatic reconnection with exponential backoff.

    Implements a robust reconnection strategy with exponential backoff
    to handle transient network issues and API interruptions.
    """

    # Reconnection configuration constants
    MAX_RETRIES: int = 5
    BASE_DELAY: float = 1.0  # seconds
    MAX_DELAY: float = 30.0  # seconds
    BACKOFF_MULTIPLIER: float = 2.0

    def __init__(self, max_retries: int = MAX_RETRIES):
        """
        Initialize reconnection handler.

        Args:
            max_retries: Maximum number of reconnection attempts
        """
        self._max_retries = max_retries
        self._retry_count = 0
        self._state = ReconnectionState.IDLE

    def reset(self) -> None:
        """Reset reconnection state and retry counter."""
        self._retry_count = 0
        self._state = ReconnectionState.IDLE

    @property
    def state(self) -> ReconnectionState:
        """Current reconnection state."""
        return self._state

    @property
    def retry_count(self) -> int:
        """Number of reconnection attempts made."""
        return self._retry_count

    def _calculate_delay(self) -> float:
        """
        Calculate exponential backoff delay with jitter.

        Adds random jitter to prevent thundering herd problem when
        multiple clients reconnect simultaneously.

        Returns:
            Delay in seconds for next retry attempt
        """
        # Calculate base exponential backoff
        delay = self.BASE_DELAY * (self.BACKOFF_MULTIPLIER**self._retry_count)
        delay = min(delay, self.MAX_DELAY)

        # Add jitter: randomize between 50% and 100% of calculated delay
        jitter = random.uniform(0.5, 1.0)
        return delay * jitter

    async def reconnect_with_backoff(
        self,
        connect_func: Callable[[], Awaitable[None]],
        on_retry: Optional[Callable[[int, float], Awaitable[None]]] = None,
    ) -> bool:
        """
        Attempt reconnection with exponential backoff.

        Args:
            connect_func: Async function to call for connection
            on_retry: Optional callback called before each retry attempt.
                     Receives (retry_number, delay_seconds) as arguments.

        Returns:
            True if reconnection successful, False if max retries exceeded

        Example:
            ```python
            handler = ReconnectionHandler()

            async def connect():
                await client.connect()

            async def on_retry_callback(attempt: int, delay: float):
                print(f"Retry {attempt} in {delay}s...")

            success = await handler.reconnect_with_backoff(
                connect, on_retry_callback
            )
            ```
        """
        self._state = ReconnectionState.CONNECTING
        self._retry_count = 0

        while self._retry_count < self._max_retries:
            try:
                # Calculate delay before attempt (except first attempt)
                if self._retry_count > 0:
                    delay = self._calculate_delay()
                    logger.info(
                        f"Reconnection attempt {self._retry_count + 1}/{self._max_retries} "
                        f"in {delay:.1f}s..."
                    )

                    # Call retry callback if provided
                    if on_retry:
                        await on_retry(self._retry_count + 1, delay)

                    await asyncio.sleep(delay)
                else:
                    logger.info("Initial connection attempt...")

                # Attempt connection
                await connect_func()

                # Success!
                logger.info("Connection established successfully")
                self._state = ReconnectionState.CONNECTED
                self.reset()
                return True

            except GeminiAuthenticationError as e:
                # Authentication errors are not transient - fail immediately
                logger.error(f"Authentication failed: {e}")
                self._state = ReconnectionState.FAILED
                return False

            except (GeminiConnectionError, GeminiAudioError, Exception) as e:
                # Transient errors - retry with backoff
                self._retry_count += 1
                logger.warning(
                    f"Connection attempt {self._retry_count} failed: {e}"
                )

                if self._retry_count >= self._max_retries:
                    logger.error(
                        f"Max retries ({self._max_retries}) exceeded. Giving up."
                    )
                    self._state = ReconnectionState.FAILED
                    return False

        # Should not reach here, but just in case
        self._state = ReconnectionState.FAILED
        return False


class SessionTimeoutTracker:
    """
    Tracks session duration to proactively reconnect before timeout.

    Gemini Live API sessions typically expire after 10 minutes. This tracker
    monitors session duration and triggers reconnection before expiry.
    """

    DEFAULT_SESSION_TIMEOUT: float = 600.0  # 10 minutes in seconds
    RECONNECT_BUFFER: float = 30.0  # Reconnect 30s before timeout

    def __init__(self, session_timeout: float = DEFAULT_SESSION_TIMEOUT):
        """
        Initialize session timeout tracker.

        Args:
            session_timeout: Session timeout in seconds (default 10 minutes)
        """
        self._session_timeout = session_timeout
        self._session_start_time: Optional[float] = None

    def start_session(self) -> None:
        """Mark the start of a new session."""
        self._session_start_time = asyncio.get_running_loop().time()
        logger.debug("Session timeout tracking started")

    def end_session(self) -> None:
        """Mark the end of the current session."""
        self._session_start_time = None
        logger.debug("Session timeout tracking ended")

    def get_session_duration(self) -> float:
        """
        Get current session duration in seconds.

        Returns:
            Duration in seconds, or 0.0 if no active session
        """
        if self._session_start_time is None:
            return 0.0

        current_time = asyncio.get_running_loop().time()
        return current_time - self._session_start_time

    def should_reconnect(self) -> bool:
        """
        Check if session should be proactively reconnected.

        Returns:
            True if session is approaching timeout, False otherwise
        """
        if self._session_start_time is None:
            return False

        duration = self.get_session_duration()
        timeout_threshold = self._session_timeout - self.RECONNECT_BUFFER

        if duration >= timeout_threshold:
            logger.warning(
                f"Session approaching timeout ({duration:.1f}s / {self._session_timeout:.1f}s). "
                "Proactive reconnection recommended."
            )
            return True

        return False

    def time_until_reconnect(self) -> float:
        """
        Calculate time until proactive reconnection should occur.

        Returns:
            Seconds until reconnection needed, or -1.0 if already past threshold
        """
        if self._session_start_time is None:
            return float("inf")

        duration = self.get_session_duration()
        timeout_threshold = self._session_timeout - self.RECONNECT_BUFFER
        return max(0.0, timeout_threshold - duration)
