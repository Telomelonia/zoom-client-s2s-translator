#!/usr/bin/env python3
"""
Minimal test to check if we have access to Gemini S2ST model.
Run this AFTER enabling Vertex AI API.
"""

import asyncio
import os
from pathlib import Path

# Suppress warnings for cleaner output
import warnings
warnings.filterwarnings("ignore")

# Load .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

async def test_s2st_access():
    """Test if we can connect to the S2ST model."""

    print("=" * 50)
    print("GEMINI S2ST ACCESS TEST")
    print("=" * 50)

    # Check for google-genai package
    try:
        from google import genai
        from google.genai import types
        print("✓ google-genai package found")
    except ImportError:
        print("✗ google-genai package NOT found")
        print("  Run: pip install google-genai")
        return False

    # Check GCP project
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        print("✗ GOOGLE_CLOUD_PROJECT not set in .env")
        return False
    print(f"✓ Using GCP project: {project}")

    # S2ST model name (must be set in .env)
    MODEL = os.environ.get("GEMINI_MODEL")
    if not MODEL:
        print("✗ GEMINI_MODEL not set in .env")
        return False
    print(f"✓ Testing model: {MODEL}")

    print("\n" + "-" * 50)
    print("Attempting to connect...")
    print("-" * 50 + "\n")

    try:
        # Initialize Vertex AI client
        client = genai.Client(
            vertexai=True,
            project=project,
            location="us-central1",
        )
        print("✓ Client initialized")

        # Create minimal config for S2ST
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                language_code="ja"  # Japanese as target
            ),
        )
        print("✓ Config created")

        # Try to connect
        print("→ Connecting to Live API...")

        async with client.aio.live.connect(model=MODEL, config=config) as session:
            print("\n" + "=" * 50)
            print("🎉 SUCCESS! S2ST MODEL IS ACCESSIBLE!")
            print("=" * 50)
            print(f"\nModel: {MODEL}")
            print("Status: Connected successfully")
            print("\nYou have access to speech-to-speech translation!")
            print("No allowlist blocking detected.")
            return True

    except Exception as e:
        error_str = str(e).lower()

        print("\n" + "=" * 50)
        print("CONNECTION RESULT")
        print("=" * 50)

        if "not found" in error_str or "404" in error_str:
            print("✗ Model not found")
            print("  The model name might be incorrect or not available in your region")
        elif "permission" in error_str or "403" in error_str:
            print("✗ Permission denied")
            print("  You may need allowlist access for this model")
        elif "allowlist" in error_str or "not allowlisted" in error_str:
            print("✗ NOT ALLOWLISTED")
            print("  This model requires special access from Google")
        elif "authentication" in error_str or "401" in error_str:
            print("✗ Authentication failed")
            print("  Run: gcloud auth application-default login")
        elif "api not enabled" in error_str or "aiplatform" in error_str:
            print("✗ Vertex AI API not enabled")
            print("  Run: gcloud services enable aiplatform.googleapis.com")
        else:
            print(f"✗ Error: {e}")

        print("\n" + "-" * 50)
        print("Full error details:")
        print(str(e))
        print("-" * 50)

        return False


if __name__ == "__main__":
    result = asyncio.run(test_s2st_access())

    print("\n" + "=" * 50)
    if result:
        print("NEXT STEP: You can use the S2ST model for real-time translation!")
    else:
        print("NEXT STEP: Check error above and troubleshoot")
    print("=" * 50)
