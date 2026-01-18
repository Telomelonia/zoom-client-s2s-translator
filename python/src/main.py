"""
Main entry point for the Python backend.

This module serves as the bridge between the Electron frontend and the
Python audio processing pipeline. It handles IPC communication and
coordinates the translation services.
"""

import asyncio
import logging
import sys
from typing import NoReturn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


async def main() -> NoReturn:
    """
    Main application entry point.

    Sets up the IPC server and starts the event loop.
    """
    logger.info("Starting Zoom S2S Translator backend v0.1.0")

    try:
        # TODO: Initialize IPC server
        # TODO: Initialize audio subsystem
        # TODO: Initialize Gemini client

        logger.info("Backend initialized successfully")

        # Keep the event loop running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.exception("Fatal error in main loop: %s", e)
        sys.exit(1)
    finally:
        logger.info("Backend shutting down")


if __name__ == "__main__":
    asyncio.run(main())
